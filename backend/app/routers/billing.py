from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.transaction import Transaction, BillingItem
from app.models.medicine import Medicine
from app.services.receipt_generator import generate_receipt
from app.config import RECEIPTS_FOLDER
import datetime

router = APIRouter(
    prefix="/billing",
    tags=["billing"]
)


# ─── REQUEST MODELS ──────────────────────────────────────
class BillItemRequest(BaseModel):
    medicine_id:    int
    quantity:       int           # number of tablets/units customer wants
    use_per_unit:   bool = False  # True = sell per tablet, False = per strip


class CreateBillRequest(BaseModel):
    items:             List[BillItemRequest]
    discount_percent:  Optional[float] = None  # e.g. 10 means 10% off
    discount_flat:     Optional[float] = None  # e.g. 50 means ৳50 off


# ─── CREATE A BILL ───────────────────────────────────────
@router.post("/create")
def create_bill(
    request: CreateBillRequest,
    db: Session = Depends(get_db)
):
    """
    Creates a complete bill.

    Supports:
    - Full strip or per tablet/unit pricing
    - Optional percentage discount
    - Optional flat discount amount

    Example:
    {
        "items": [
            {
                "medicine_id": 1,
                "quantity": 4,
                "use_per_unit": true    ← selling 4 tablets from strip
            },
            {
                "medicine_id": 2,
                "quantity": 2,
                "use_per_unit": false   ← selling 2 full strips
            }
        ],
        "discount_percent": 10,         ← 10% off total (optional)
        "discount_flat": null           ← no flat discount
    }
    """

    if not request.items:
        raise HTTPException(
            status_code=400,
            detail="Bill must have at least one item"
        )

    subtotal   = 0.0
    bill_items = []

    for item in request.items:
        medicine = db.query(Medicine).filter(
            Medicine.id == item.medicine_id
        ).first()

        if not medicine:
            raise HTTPException(
                status_code=404,
                detail=f"Medicine ID {item.medicine_id} not found"
            )

        if item.quantity <= 0:
            raise HTTPException(
                status_code=400,
                detail="Quantity must be greater than 0"
            )

        strip_price = medicine.unit_price or 0.0
        pack_size   = medicine.pack_size  or 1

        # ── Calculate unit price ──────────────────────────
        if item.use_per_unit and pack_size > 1:
            # Selling per tablet/capsule
            price_per_unit = round(strip_price / pack_size, 2)
            pricing_note   = f"৳{strip_price} ÷ {pack_size} units = " \
                             f"৳{price_per_unit}/unit"
        else:
            # Selling full strips
            price_per_unit = strip_price
            pricing_note   = f"৳{strip_price}/strip"

        total_price = round(price_per_unit * item.quantity, 2)
        subtotal   += total_price

        bill_items.append({
            "medicine_id":   medicine.id,
            "medicine_name": f"{medicine.brand_name} "
                            f"{medicine.strength or ''}".strip(),
            "manufacturer":  medicine.manufacturer,
            "quantity":      item.quantity,
            "unit_type":     "tablet" if item.use_per_unit else "strip",
            "unit_price":    price_per_unit,
            "total_price":   total_price,
            "pricing_note":  pricing_note
        })

    # ── Apply discount if provided ────────────────────────
    subtotal         = round(subtotal, 2)
    discount_amount  = 0.0
    discount_note    = None

    if request.discount_percent and request.discount_percent > 0:
        # Percentage discount — e.g. 10% off
        discount_amount = round(subtotal * request.discount_percent / 100, 2)
        discount_note   = f"{request.discount_percent}% discount"

    elif request.discount_flat and request.discount_flat > 0:
        # Flat discount — e.g. ৳50 off
        discount_amount = min(
            round(request.discount_flat, 2),
            subtotal  # discount can't exceed total
        )
        discount_note = f"Flat ৳{discount_amount} discount"

    total_after_discount = round(subtotal - discount_amount, 2)

    # ── Save transaction to database ──────────────────────
    transaction = Transaction(
        created_at   = datetime.datetime.utcnow(),
        total_amount = total_after_discount
    )
    db.add(transaction)
    db.flush()

    # Save each billing item
    for item_data in bill_items:
        billing_item = BillingItem(
            transaction_id = transaction.id,
            medicine_id    = item_data['medicine_id'],
            medicine_name  = item_data['medicine_name'],
            quantity       = item_data['quantity'],
            unit_price     = item_data['unit_price'],
            total_price    = item_data['total_price']
        )
        db.add(billing_item)

    db.commit()
    db.refresh(transaction)

    # ── Build response ────────────────────────────────────
    response = {
        "success":        True,
        "transaction_id": transaction.id,
        "created_at":     str(transaction.created_at),
        "items":          bill_items,
        "subtotal":       subtotal,
    }

    # Only show discount info if discount was applied
    if discount_amount > 0:
        response["discount_note"]   = discount_note
        response["discount_amount"] = discount_amount

    response["total_amount"] = total_after_discount
    response["item_count"]   = len(bill_items)

    return response


# ─── GET BILL BY ID ──────────────────────────────────────
@router.get("/{transaction_id}")
def get_bill(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    items = db.query(BillingItem).filter(
        BillingItem.transaction_id == transaction_id
    ).all()

    return {
        "transaction_id": transaction.id,
        "created_at":     str(transaction.created_at),
        "total_amount":   transaction.total_amount,
        "items": [
            {
                "medicine_name": item.medicine_name,
                "quantity":      item.quantity,
                "unit_price":    item.unit_price,
                "total_price":   item.total_price
            }
            for item in items
        ]
    }


# ─── GET ALL BILLS ───────────────────────────────────────
@router.get("/")
def get_all_bills(
    skip:  int = 0,
    limit: int = 20,
    db:    Session = Depends(get_db)
):
    transactions = db.query(Transaction)\
        .order_by(Transaction.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()

    return {
        "total": len(transactions),
        "bills": [
            {
                "transaction_id": t.id,
                "created_at":     str(t.created_at),
                "total_amount":   t.total_amount
            }
            for t in transactions
        ]
    }


# ─── GENERATE RECEIPT PDF ────────────────────────────────
@router.get("/{transaction_id}/receipt")
def download_receipt(
    transaction_id: int,
    db: Session = Depends(get_db)
):
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    items = db.query(BillingItem).filter(
        BillingItem.transaction_id == transaction_id
    ).all()

    transaction_data = {
        "transaction_id": transaction.id,
        "created_at":     str(transaction.created_at),
        "total_amount":   transaction.total_amount,
        "items": [
            {
                "medicine_name": item.medicine_name,
                "quantity":      item.quantity,
                "unit_price":    item.unit_price  or 0.0,
                "total_price":   item.total_price or 0.0
            }
            for item in items
        ]
    }

    pdf_path = generate_receipt(transaction_data, RECEIPTS_FOLDER)

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"receipt_{transaction_id}.pdf"
    )