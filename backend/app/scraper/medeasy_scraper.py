import asyncio
import re
import sys
import os
from datetime import date

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from playwright.async_api import async_playwright
from app.database import SessionLocal, engine, Base
from app.models.medicine import Medicine

Base.metadata.create_all(bind=engine)

# ─── SETTINGS ───────────────────────────────────────────
# Add as many categories as you want here
CATEGORIES = [
    {
        "name":      "Prescription Medicine",
        "url":       "https://medeasy.health/prescription-medicine",
        "max_pages": 500
    },
    {
        "name":      "OTC Medicine",
        "url":       "https://medeasy.health/otc-medicine",
        "max_pages": 1000
    },
]

DELAY = 3  # seconds between pages


# ─── PARSE MEDICINE LIST PAGE ───────────────────────────
def parse_medicines_from_text(text):
    medicines = []
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    i = 0
    while i < len(lines):
        # Look for discount line as start of medicine block
        if re.match(r'^\d+%\s*Off$', lines[i]):
            try:
                raw_name     = lines[i + 1]
                manufacturer = lines[i + 2]

                # Price lines — handle both "৳ 10.08" and "৳\n10.08"
                price_line_1 = lines[i + 3].replace('৳', '').strip()
                price_line_2 = lines[i + 4].replace('৳', '').strip()

                # If price_line_1 is empty, the ৳ and number were split
                if price_line_1 == '':
                    price_disc = lines[i + 4].replace('৳', '').strip()
                    price_orig = lines[i + 5].replace('৳', '').strip()
                    skip = 7
                else:
                    price_disc = price_line_1
                    price_orig = price_line_2
                    skip = 6

                # Split brand name and strength
                # "Ecosprin75 mg" → "Ecosprin" + "75 mg"
                match = re.match(r'^([A-Za-z\s\-]+?)(\d+.*)', raw_name)
                if match:
                    brand_name = match.group(1).strip()
                    strength   = match.group(2).strip()
                else:
                    brand_name = raw_name
                    strength   = ""

                # Clean and convert price to float
                try:
                    unit_price = float(
                        re.sub(r'[^\d.]', '', price_disc)
                    )
                    # Sanity check — ignore clearly wrong prices
                    if unit_price <= 0 or unit_price > 100000:
                        unit_price = None
                except:
                    unit_price = None

                medicines.append({
                    "brand_name":   brand_name,
                    "strength":     strength,
                    "manufacturer": manufacturer,
                    "unit_price":   unit_price,
                    "source":       "medeasy.health",
                    "last_updated": str(date.today())
                })

                i += skip
                continue

            except IndexError:
                pass

        i += 1

    return medicines


# ─── GET DETAILS FROM INDIVIDUAL MEDICINE PAGE ──────────
async def get_medicine_details(page, url):
    details = {
        "generic_name": None,
        "pack_size":    None,
        "form":         None,
        "image_url":    None
    }

    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(1500)

        text  = await page.inner_text("body")
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # Look for generic name
        for j, line in enumerate(lines):
            if "generic" in line.lower() and j + 1 < len(lines):
                details["generic_name"] = lines[j + 1]
                break

        # Look for pack size and form
        for line in lines:
            match = re.search(
                r'(\d+)\s*(pcs|tablets?|capsules?|ml|mg)',
                line, re.IGNORECASE
            )
            if match:
                details["pack_size"] = int(match.group(1))
                details["form"]      = match.group(2).lower()
                break

        # Get product image
        img = await page.query_selector(
            "img.product-image, img.medicine-image, .product img"
        )
        if img:
            details["image_url"] = await img.get_attribute("src")

    except Exception as e:
        print(f"      Detail page error: {e}")

    return details


# ─── SAVE TO DATABASE ────────────────────────────────────
def save_to_database(medicines):
    db      = SessionLocal()
    saved   = 0
    updated = 0
    skipped = 0

    try:
        for med in medicines:
            existing = db.query(Medicine).filter(
                Medicine.brand_name == med['brand_name'],
                Medicine.strength   == med['strength']
            ).first()

            if existing:
                # Update missing fields if we now have them
                changed = False
                if med.get('unit_price') and not existing.unit_price:
                    existing.unit_price = med['unit_price']
                    changed = True
                if med.get('generic_name') and not existing.generic_name:
                    existing.generic_name = med['generic_name']
                    changed = True
                if med.get('pack_size') and not existing.pack_size:
                    existing.pack_size = med['pack_size']
                    changed = True
                if med.get('form') and not existing.form:
                    existing.form = med['form']
                    changed = True
                if med.get('image_url') and not existing.image_url:
                    existing.image_url = med['image_url']
                    changed = True
                if changed:
                    existing.last_updated = med['last_updated']
                    updated += 1
                else:
                    skipped += 1
                continue

            # Save new medicine
            new_medicine = Medicine(
                brand_name   = med['brand_name'],
                strength     = med['strength'],
                manufacturer = med['manufacturer'],
                unit_price   = med.get('unit_price'),
                generic_name = med.get('generic_name'),
                pack_size    = med.get('pack_size'),
                form         = med.get('form', 'tablet'),
                image_url    = med.get('image_url'),
                source       = med['source'],
                last_updated = med['last_updated']
            )
            db.add(new_medicine)
            saved += 1

        db.commit()

    except Exception as e:
        db.rollback()
        print(f"    Database error: {e}")

    finally:
        db.close()

    print(f"    Saved: {saved} | Updated: {updated} | Skipped: {skipped}")
    return saved


# ─── SCRAPE ONE CATEGORY ─────────────────────────────────
async def scrape_category(browser, category):
    name      = category['name']
    base_url  = category['url']
    max_pages = category['max_pages']

    print(f"\n{'='*40}")
    print(f"  Starting: {name}")
    print(f"  URL     : {base_url}")
    print(f"  Pages   : {max_pages}")
    print(f"{'='*40}")

    total_saved = 0
    list_page   = await browser.new_page()
    detail_page = await browser.new_page()

    for page_num in range(1, max_pages + 1):
        url = f"{base_url}?page={page_num}"
        print(f"\n  Page {page_num}/{max_pages}: {url}")

        try:
            await list_page.goto(
                url, wait_until="networkidle", timeout=30000
            )
            await list_page.wait_for_timeout(2000)

            # Get medicine links for detail pages
            links = await list_page.eval_on_selector_all(
                "a[href*='/medicine/'], a[href*='/product/']",
                "els => els.map(e => e.href)"
            )

            # Parse basic info
            text      = await list_page.inner_text("body")
            medicines = parse_medicines_from_text(text)
            print(f"    Found: {len(medicines)} medicines")

            if len(medicines) == 0:
                print(f"    No medicines found — stopping {name}")
                break

            # Get extra details from individual pages
            if links:
                print(f"    Fetching details from product pages...")
                for idx, med in enumerate(medicines):
                    if idx < len(links):
                        details = await get_medicine_details(
                            detail_page, links[idx]
                        )
                        med.update(details)
                    await asyncio.sleep(1)

            saved = save_to_database(medicines)
            total_saved += saved

            print(f"    Waiting {DELAY} seconds...")
            await asyncio.sleep(DELAY)

        except Exception as e:
            print(f"    Error on page {page_num}: {e}")
            continue

    await list_page.close()
    await detail_page.close()

    print(f"\n  Finished: {name}")
    print(f"  Total saved: {total_saved}")
    return total_saved


# ─── MAIN ────────────────────────────────────────────────
async def scrape_all():
    grand_total = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        for category in CATEGORIES:
            saved       = await scrape_category(browser, category)
            grand_total += saved

        await browser.close()

    print(f"\n{'='*40}")
    print(f"  ALL DONE!")
    print(f"  Grand total saved: {grand_total}")
    print(f"{'='*40}")


# ─── RUN ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("="*40)
    print("  MedEasy Full Scraper")
    print(f"  Categories: {len(CATEGORIES)}")
    print("="*40)
    asyncio.run(scrape_all())