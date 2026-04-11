from rapidfuzz import fuzz
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.medicine import Medicine
from app.models.medicine_unified import MedicineUnified
import re


def normalize_name(name: str) -> str:
    if not name:
        return ""

    name = name.lower().strip()

    ocr_fixes = {
        'c-ralex': 'coralex',
        'ceralex': 'coralex',
        'nopa':    'napa',
        'secto':   'seclo',
        '4q0':     '400',
        'amodas':  'amodis',
        'diaklt':  'diakit',
        'apldone': 'apidone',
    }

    for wrong, correct in ocr_fixes.items():
        name = name.replace(wrong, correct)

    name = re.sub(r'(\d)Q(\d)', r'\g<1>0\2', name)
    name = re.sub(r'(\d)Q\b',   r'\g<1>0',   name)
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return name


def get_candidates_from_unified(query: str, db: Session):
    """Search the unified table first — covers all sources."""
    words = [w for w in query.split() if len(w) > 1]

    if not words:
        return []

    filters = [
        MedicineUnified.brand_name.ilike(f"%{word}%")
        for word in words
    ]

    if words:
        first_word = words[0]
        if len(first_word) >= 3:
            filters.append(
                MedicineUnified.brand_name.ilike(f"{first_word[:4]}%")
            )
        if len(first_word) >= 3:
            filters.append(
                MedicineUnified.brand_name.ilike(f"{first_word[:3]}%")
            )

    candidates = db.query(MedicineUnified).filter(
        or_(*filters)
    ).limit(300).all()

    return candidates


def get_all_candidates(query: str, db: Session):
    words = [w for w in query.split() if len(w) > 1]

    if not words:
        return db.query(Medicine).limit(500).all()

    filters = [
        Medicine.brand_name.ilike(f"%{word}%")
        for word in words
    ]

    if words:
        first_word = words[0]
        if len(first_word) >= 3:
            filters.append(
                Medicine.brand_name.ilike(f"{first_word[:4]}%")
            )
        if len(first_word) >= 3:
            filters.append(
                Medicine.brand_name.ilike(f"{first_word[:3]}%")
            )

    candidates = db.query(Medicine).filter(
        or_(*filters)
    ).limit(300).all()

    if len(candidates) < 10:
        fallback = db.query(Medicine).limit(500).all()
        existing_ids = {c.id for c in candidates}
        for m in fallback:
            if m.id not in existing_ids:
                candidates.append(m)

    return candidates


def multi_score(query: str, medicine_str: str) -> float:
    query_norm = normalize_name(query)
    med_norm   = normalize_name(medicine_str)

    query_first = query_norm.split()[0] if query_norm.split() else query_norm
    med_first   = med_norm.split()[0]   if med_norm.split()   else med_norm

    score1 = fuzz.token_sort_ratio(query_norm, med_norm)
    score2 = fuzz.partial_ratio(query_norm, med_norm)
    score3 = fuzz.token_set_ratio(query_norm, med_norm)
    score4 = fuzz.ratio(query_norm, med_norm)
    brand_score = fuzz.ratio(query_first, med_first)

    combined = (
        score1      * 0.20 +
        score2      * 0.20 +
        score3      * 0.20 +
        score4      * 0.10 +
        brand_score * 0.30
    )

    return round(combined, 1)


def search_medicines(query: str, db: Session, limit: int = 3):
    if not query or len(query.strip()) < 2:
        return []

    query            = query.strip()
    normalized_query = normalize_name(query)
    print(f"Normalized query: '{normalized_query}'")

    # Try unified table first
    unified_candidates = get_candidates_from_unified(normalized_query, db)
    print(f"Unified candidates: {len(unified_candidates)}")

    matched = []

    if unified_candidates:
        scored = []
        for med in unified_candidates:
            med_str     = f"{med.brand_name} {med.strength or ''}".strip()
            score       = multi_score(query, med_str)
            name_score  = multi_score(query, med.brand_name or '')
            final_score = max(score, name_score)
            scored.append((med, final_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:limit]

        for med, score in top:
            matched.append({
                "id":           med.source_id,
                "brand_name":   med.brand_name,
                "generic_name": med.generic_name,
                "manufacturer": med.manufacturer or med.source,
                "strength":     med.strength,
                "form":         med.form,
                "unit_price":   med.unit_price,
                "confidence":   score,
                "source":       med.source,
                "auto_confirm": score >= 85
            })

        if matched:
            return matched

    # Fallback to original medicines table
    print("Falling back to original medicines table...")
    candidates = get_all_candidates(normalized_query, db)
    print(f"Original candidates: {len(candidates)}")

    if not candidates:
        return []

    scored = []
    for med in candidates:
        med_str     = f"{med.brand_name} {med.strength or ''}".strip()
        score       = multi_score(query, med_str)
        name_score  = multi_score(query, med.brand_name or '')
        final_score = max(score, name_score)
        scored.append((med, final_score))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:limit]

    for med, score in top:
        matched.append({
            "id":           med.id,
            "brand_name":   med.brand_name,
            "generic_name": med.generic_name,
            "manufacturer": med.manufacturer,
            "strength":     med.strength,
            "form":         med.form,
            "unit_price":   med.unit_price,
            "confidence":   score,
            "source":       "medeasy",
            "auto_confirm": score >= 85
        })

    return matched


def get_medicine_by_id(medicine_id: int, db: Session):
    return db.query(Medicine).filter(
        Medicine.id == medicine_id
    ).first()


def get_medicine_by_barcode(barcode: str, db: Session):
    return db.query(Medicine).filter(
        Medicine.barcode == barcode
    ).first()