from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.services.preprocessor import base64_to_image, preprocess_image
from app.services.ocr_engine import extract_text, build_search_query
from app.services.fuzzy_matcher import search_medicines, get_medicine_by_barcode
import traceback
import cv2
import os

router = APIRouter(
    prefix="/detect",
    tags=["detection"]
)


class ImageBase64Request(BaseModel):
    image: str


class BarcodeRequest(BaseModel):
    barcode: str


@router.post("/ocr")
def detect_from_image(
    request: ImageBase64Request,
    db: Session = Depends(get_db)
):
    try:
        img = base64_to_image(request.image)
        if img is None:
            raise HTTPException(status_code=400, detail="Could not decode image")

        print(f"Image shape: {img.shape}")
        processed = preprocess_image(img)
        print(f"Processed shape: {processed.shape}")

        # Save debug image
        cv2.imwrite("debug_capture.png", processed)
        print(f"Debug saved to: {os.path.abspath('debug_capture.png')}")

        print("Running OCR...")
        ocr_results = extract_text(processed)

        if not ocr_results:
            return {
                "success":     False,
                "message":     "No text found — try better lighting",
                "ocr_results": [],
                "query":       "",
                "results":     []
            }

        query = build_search_query(ocr_results)
        print(f"Search query: {query}")

        if not query:
            return {
                "success":     False,
                "message":     "Could not identify medicine name",
                "ocr_results": ocr_results,
                "query":       "",
                "results":     []
            }

        matches = search_medicines(query, db, limit=3)
        print(f"Matches returned: {len(matches)}")
        for m in matches:
            print(f"  → {m['brand_name']} {m['strength']} | score: {m['confidence']}")

        return {
            "success":     len(matches) > 0,
            "ocr_results": ocr_results,
            "query":       query,
            "results":     matches,
            "message":     f"Found {len(matches)} matches for '{query}'"
        }

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Detection error: {str(e)}")


@router.post("/barcode")
def detect_from_barcode(
    request: BarcodeRequest,
    db: Session = Depends(get_db)
):
    medicine = get_medicine_by_barcode(request.barcode, db)
    if not medicine:
        return {
            "success": False,
            "message": f"No medicine found for barcode: {request.barcode}",
            "results": []
        }
    return {
        "success": True,
        "message": "Medicine found by barcode",
        "results": [{
            "id":           medicine.id,
            "brand_name":   medicine.brand_name,
            "generic_name": medicine.generic_name,
            "manufacturer": medicine.manufacturer,
            "strength":     medicine.strength,
            "form":         medicine.form,
            "unit_price":   medicine.unit_price,
            "confidence":   100,
            "auto_confirm": True
        }]
    }


@router.get("/test")
def test_ocr():
    try:
        import easyocr
        return {"success": True, "message": "OCR engine is loaded and ready"}
    except Exception as e:
        return {"success": False, "message": f"OCR engine error: {str(e)}"}