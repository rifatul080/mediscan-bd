import ssl
ssl._create_default_https_context = ssl._create_unverified_context

import easyocr
import re
import cv2

print("Loading OCR engine...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)
print("OCR engine ready!")


def extract_text(processed_image) -> list:
    all_texts = {}

    # Attempt 1 — normal
    try:
        results = reader.readtext(processed_image)
        for (bbox, text, confidence) in results:
            text = text.strip()
            if confidence > 0.05 and len(text) > 1:
                key = text.lower()
                if key not in all_texts or \
                   all_texts[key]['confidence'] < confidence * 100:
                    all_texts[key] = {
                        "text":       text,
                        "confidence": round(confidence * 100, 1)
                    }
    except Exception as e:
        print(f"OCR attempt 1 failed: {e}")

    # Attempt 2 — paragraph mode
    try:
        results2 = reader.readtext(processed_image, paragraph=True)
        for (bbox, text, confidence) in results2:
            text = text.strip()
            if confidence > 0.05 and len(text) > 1:
                key = text.lower()
                if key not in all_texts:
                    all_texts[key] = {
                        "text":       text,
                        "confidence": round(confidence * 100, 1)
                    }
    except Exception:
        pass

    # Attempt 3 — inverted image
    try:
        inverted = cv2.bitwise_not(processed_image)
        results3 = reader.readtext(inverted)
        for (bbox, text, confidence) in results3:
            text = text.strip()
            if confidence > 0.05 and len(text) > 1:
                key = text.lower()
                if key not in all_texts:
                    all_texts[key] = {
                        "text":       text,
                        "confidence": round(confidence * 100, 1)
                    }
    except Exception:
        pass

    texts = list(all_texts.values())
    print(f"OCR found {len(texts)} text blocks")
    if texts:
        print("OCR text blocks:")
        for t in texts:
            print(f"  [{t['confidence']}%] {t['text']}")

    return texts


def extract_medicine_name(ocr_results: list) -> str:
    if not ocr_results:
        return ""

    ignore_words = {
        'tablets', 'capsules', 'syrup', 'injection',
        'manufactured', 'mfg', 'exp', 'batch', 'lot',
        'store', 'keep', 'away', 'children', 'shake',
        'well', 'before', 'use', 'date', 'ltd', 'pvt',
        'pharmaceuticals', 'pharma', 'lab', 'laboratories',
        'directions', 'dosage', 'adult', 'each', 'contains',
        'warning', 'caution', 'bangladesh', 'dhaka'
    }

    dosage_pattern = re.compile(
        r'\d+\s*(mg|ml|mcg|iu|g)\b', re.IGNORECASE
    )

    candidates = []

    for item in ocr_results:
        text  = item['text']
        conf  = item['confidence']
        lower = text.lower().strip()

        if lower in ignore_words:
            continue
        if text.replace('.', '').replace(',', '').isdigit():
            continue
        if len(text) < 3:
            continue

        score = conf
        if dosage_pattern.search(text):
            score += 10

        candidates.append({"text": text, "score": score})

    if not candidates:
        return ""

    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[0]['text']


def build_search_query(ocr_results: list) -> str:
    if not ocr_results:
        return ""

    dosage_pattern = re.compile(
        r'\d+\s*(mg|ml|mcg|iu|g)\b', re.IGNORECASE
    )

    # Filter low confidence and short results
    clean_results = [
        r for r in ocr_results
        if len(r['text']) >= 3 and r['confidence'] >= 15
    ]

    if not clean_results:
        clean_results = ocr_results

    clean_results.sort(key=lambda x: x['confidence'], reverse=True)

    name_part   = extract_medicine_name(ocr_results)
    dosage_part = ""

    for item in ocr_results:
        match = dosage_pattern.search(item['text'])
        if match:
            dosage_part = match.group(0)
            break

    query = f"{name_part} {dosage_part}".strip()
    print(f"Built search query: '{query}'")
    return query