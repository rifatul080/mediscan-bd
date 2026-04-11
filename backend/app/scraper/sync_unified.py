"""
Syncs all medicine sources into the unified medicines_unified table.
Run this after scraping any source.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy.orm import Session
from app.database import engine, Base
from app.models.medicine import Medicine
from app.models.medicine_chaldal import MedicineChaldal
from app.models.medicine_unified import MedicineUnified

Base.metadata.create_all(bind=engine)


def sync_unified():
    db = Session(bind=engine)

    print("Syncing unified medicines table...")

    # Clear existing unified table
    db.query(MedicineUnified).delete()
    db.commit()

    total = 0

    # ── Source 1: MedEasy ────────────────────────────────
    print("Adding MedEasy medicines...")
    medeasy = db.query(Medicine).all()
    for m in medeasy:
        unified = MedicineUnified(
            source_id    = m.id,
            source       = 'medeasy',
            brand_name   = m.brand_name,
            generic_name = m.generic_name,
            manufacturer = m.manufacturer,
            strength     = m.strength,
            form         = m.form,
            unit_price   = m.unit_price,
            unit         = None,
            category     = None,
            image_url    = m.image_url if hasattr(m, 'image_url') else None,
            product_url  = None
        )
        db.add(unified)
        total += 1

    db.commit()
    print(f"  Added {len(medeasy)} MedEasy medicines")

    # ── Source 2: Chaldal ────────────────────────────────
    try:
        print("Adding Chaldal medicines...")
        chaldal = db.query(MedicineChaldal).all()
        for m in chaldal:
            unified = MedicineUnified(
                source_id    = m.id,
                source       = 'chaldal',
                brand_name   = m.name,
                generic_name = None,
                manufacturer = None,
                strength     = None,
                form         = None,
                unit_price   = m.price,
                unit         = m.unit,
                category     = m.category,
                image_url    = m.image_url,
                product_url  = m.product_url
            )
            db.add(unified)
            total += 1

        db.commit()
        print(f"  Added {len(chaldal)} Chaldal medicines")
    except Exception as e:
        print(f"  Chaldal skipped: {e}")

    db.close()
    print(f"\nUnified table ready! Total: {total} medicines")


if __name__ == '__main__':
    sync_unified()