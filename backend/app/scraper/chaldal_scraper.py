import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from sqlalchemy.orm import Session
from app.database import engine, Base
from app.models.medicine_chaldal import MedicineChaldal
import time
import re

Base.metadata.create_all(bind=engine)


def parse_price(price_str):
    if not price_str:
        return None
    nums = re.findall(r'[\d.]+', str(price_str))
    return float(nums[0]) if nums else None


def set_location(driver, wait):
    """Try to set Dhaka as delivery location."""
    try:
        print("Setting delivery location to Dhaka...")

        # Look for location input or button
        location_selectors = [
            'input[placeholder*="location"]',
            'input[placeholder*="area"]',
            'input[placeholder*="Location"]',
            '[class*="location"] input',
            '[class*="area"] input',
            '.locationInput input',
        ]

        for sel in location_selectors:
            try:
                inp = driver.find_element(By.CSS_SELECTOR, sel)
                inp.clear()
                inp.send_keys("Dhaka")
                time.sleep(1)
                inp.send_keys(Keys.RETURN)
                time.sleep(2)
                print("Location set!")
                return True
            except Exception:
                continue

        # Try clicking a location button
        btn_selectors = [
            '[class*="location"]',
            '[class*="area"]',
            'button[contains(text(), "Dhaka")]',
        ]
        for sel in btn_selectors:
            try:
                btn = driver.find_element(By.CSS_SELECTOR, sel)
                btn.click()
                time.sleep(2)
                print("Location button clicked!")
                return True
            except Exception:
                continue

        print("Could not set location automatically — continuing anyway")
        return False

    except Exception as e:
        print(f"Location setting failed: {e}")
        return False


def scroll_and_load(driver, max_scrolls=200):
    """Scroll down repeatedly until no new products load."""
    last_count  = 0
    no_change   = 0
    scroll_num  = 0

    while scroll_num < max_scrolls:
        # Scroll to bottom
        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);"
        )
        time.sleep(2)

        # Also try clicking "Load more" button if exists
        try:
            load_more = driver.find_element(
                By.CSS_SELECTOR,
                'button[class*="load"], button[class*="more"], '
                '[class*="loadMore"], [class*="load-more"]'
            )
            driver.execute_script("arguments[0].click();", load_more)
            print("  Clicked load more button")
            time.sleep(2)
        except Exception:
            pass

        # Count products
        products = []
        for sel in ['.product', '[class*="product"]', '[class*="Product"]']:
            products = driver.find_elements(By.CSS_SELECTOR, sel)
            if len(products) > 5:
                break

        current = len(products)
        print(f"  Scroll {scroll_num+1}: {current} products visible")

        if current == last_count:
            no_change += 1
            if no_change >= 8:
                print("No more products loading — done scrolling")
                break
        else:
            no_change  = 0
            last_count = current

        scroll_num += 1

    return products


def scrape_chaldal():
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--start-maximized')
    options.add_experimental_option(
        'excludeSwitches', ['enable-automation']
    )
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    driver = webdriver.Chrome(options=options)
    wait   = WebDriverWait(driver, 10)
    db     = Session(bind=engine)

    URL = "https://chaldal.com/pharmacy/all-meds"

    print(f"Opening: {URL}")
    driver.get(URL)
    time.sleep(6)

    # Try to set location
    set_location(driver, wait)
    time.sleep(3)

    # Scroll and load all products
    print("\nScrolling to load all products...")
    products = scroll_and_load(driver, max_scrolls=200)

    print(f"\nTotal products found: {len(products)}")
    print("Processing and saving to database...")

    total_scraped = 0
    total_updated = 0

    for i, product in enumerate(products):
        try:
            # Name — try multiple selectors
            name = None
            for sel in ['.name', 'h4', 'h3', 'h2',
                        '[class*="name"]', '[class*="Name"]',
                        '[class*="title"]', 'p strong', 'p']:
                try:
                    el   = product.find_element(By.CSS_SELECTOR, sel)
                    text = el.text.strip()
                    if text and len(text) > 2:
                        name = text
                        break
                except Exception:
                    continue

            if not name or len(name) < 3:
                continue

            # Price
            price = None
            for sel in ['.price', '[class*="price"]',
                        '[class*="Price"]', '.amount',
                        '[class*="amount"]']:
                try:
                    el    = product.find_element(By.CSS_SELECTOR, sel)
                    price = parse_price(el.text)
                    if price and price > 0:
                        break
                except Exception:
                    continue

            # Unit
            unit = None
            for sel in ['.unit', '.subText', '[class*="unit"]',
                        '[class*="sub"]', 'small', '.weight',
                        '[class*="weight"]']:
                try:
                    el   = product.find_element(By.CSS_SELECTOR, sel)
                    text = el.text.strip()
                    if text and text != name:
                        unit = text
                        break
                except Exception:
                    continue

            # Image
            image_url = None
            try:
                img       = product.find_element(By.TAG_NAME, 'img')
                image_url = img.get_attribute('src')
            except Exception:
                pass

            # Product URL
            product_url = None
            try:
                link        = product.find_element(By.TAG_NAME, 'a')
                product_url = link.get_attribute('href')
            except Exception:
                pass

            # Check if exists
            existing = db.query(MedicineChaldal).filter(
                MedicineChaldal.name == name
            ).first()

            if existing:
                if price and existing.price != price:
                    existing.price = price
                    db.commit()
                    total_updated += 1
                continue

            # Save
            record = MedicineChaldal(
                name        = name,
                price       = price,
                unit        = unit,
                category    = 'pharmacy',
                image_url   = image_url,
                product_url = product_url,
                source      = 'chaldal'
            )
            db.add(record)
            db.commit()
            total_scraped += 1

            if total_scraped % 25 == 0:
                print(f"  Saved {total_scraped} new records...")

        except Exception:
            continue

    driver.quit()
    db.close()

    print(f"\n✅ Done!")
    print(f"   New records saved : {total_scraped}")
    print(f"   Prices updated    : {total_updated}")
    print(f"\nNow run: python app/scraper/sync_unified.py")


if __name__ == '__main__':
    scrape_chaldal()