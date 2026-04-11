from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.fuzzy_matcher import (
    search_medicines,
    get_medicine_by_id,
    get_medicine_by_barcode
)

router = APIRouter(
    prefix="/medicines",
    tags=["medicines"]
)


@router.get("/search")
def search(query: str, db: Session = Depends(get_db)):
    """
    Search for a medicine by name.
    Returns top 3 fuzzy matches.

    Example:
        GET /medicines/search?query=napa+extra
    """
    if not query:
        raise HTTPException(
            status_code=400,
            detail="Query cannot be empty"
        )

    results = search_medicines(query, db)

    if not results:
        return {
            "found":   False,
            "query":   query,
            "results": []
        }

    return {
        "found":   True,
        "query":   query,
        "results": results
    }


@router.get("/barcode/{barcode}")
def get_by_barcode(barcode: str, db: Session = Depends(get_db)):
    """
    Get medicine by barcode.
    Returns exact match or 404 if not found.

    Example:
        GET /medicines/barcode/1234567890
    """
    medicine = get_medicine_by_barcode(barcode, db)

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail=f"No medicine found with barcode: {barcode}"
        )

    return {
        "found":    True,
        "medicine": {
            "id":           medicine.id,
            "brand_name":   medicine.brand_name,
            "generic_name": medicine.generic_name,
            "manufacturer": medicine.manufacturer,
            "strength":     medicine.strength,
            "form":         medicine.form,
            "unit_price":   medicine.unit_price,
        }
    }


@router.get("/{medicine_id}")
def get_by_id(medicine_id: int, db: Session = Depends(get_db)):
    """
    Get a single medicine by its database ID.

    Example:
        GET /medicines/1
    """
    medicine = get_medicine_by_id(medicine_id, db)

    if not medicine:
        raise HTTPException(
            status_code=404,
            detail=f"Medicine with ID {medicine_id} not found"
        )

    return {
        "id":           medicine.id,
        "brand_name":   medicine.brand_name,
        "generic_name": medicine.generic_name,
        "manufacturer": medicine.manufacturer,
        "strength":     medicine.strength,
        "form":         medicine.form,
        "unit_price":   medicine.unit_price,
        "source":       medicine.source,
        "last_updated": medicine.last_updated
    }