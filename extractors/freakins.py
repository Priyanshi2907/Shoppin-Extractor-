# freakins_xpath_scraper.py
import requests
from lxml import html
import time
from requests.exceptions import RequestException
from playwright.sync_api import sync_playwright
from PIL import Image
from io import BytesIO
import pytesseract
import re
from difflib import SequenceMatcher
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Rate Limit Handling Retries and backoff seamlessly
def fetch_with_retries(url, retries=3, backoff=1):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    for attempt in range(retries):
        try:
            response = requests.get(url,headers=headers,timeout=10)
            response.raise_for_status()
            return response
        except RequestException as e:
            print(f"[Retry {attempt+1}] Error: {e}")
            time.sleep(backoff * (2 ** attempt))
    raise Exception(f"Failed to fetch {url} after {retries} retries.")

def is_header_line(line):
    keywords = ["size", "waist", "hip", "bust", "length"]
    line_lower = line.lower()
    score = sum(1 for word in keywords if word in line_lower)
    return score >= 2  # At least 2 matching keywords

def preprocess_image(image):
    # Convert to grayscale & apply binary threshold
    gray = image.convert("L")
    return gray.point(lambda x: 0 if x < 180 else 255, '1')

def extract_table_from_image(img_bytes):
    image = Image.open(BytesIO(img_bytes))
    image = preprocess_image(image)

    text = pytesseract.image_to_string(image)
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    if not lines:
        return None

    # Find header line by keyword match
    header_idx = -1
    for i, line in enumerate(lines):
        if is_header_line(line):
            header_idx = i
            break

    if header_idx == -1:
        return {"headers": [], "rows": []}  # No valid header

    headers = re.split(r"\s{1,}", lines[header_idx])
    rows = []

    for line in lines[header_idx + 1:]:
        values = re.split(r"\s{1,}", line)
        if len(values) == len(headers):
            rows.append(dict(zip(headers, values)))

    return {
        "headers": headers,
        "rows": rows
    }


def extract_size_chart_from_product_page(product_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(product_url, timeout=15000)
            #page.click("text=Size chart", timeout=5000)

            # Use your custom XPath for the image
            img_locator = page.locator("//modal-content[contains(@class,'modal size_chart_popup_custom')]//img").first
            image_url = img_locator.get_attribute("src")

            if image_url:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                    print("img_size_chart: ",image_url)

                img_bytes = requests.get(image_url).content
                return extract_table_from_image(img_bytes)

        except Exception as e:
            print(f"Failed to extract size chart: {e}")
        finally:
            browser.close()

    return {}
def scrape_freakins():
    url = "https://freakins.com/collections/shop-womens-jeans"
    base_url = "https://freakins.com"

    response = fetch_with_retries(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {response.status_code}")

    tree = html.fromstring(response.content)
    product_cards = tree.xpath("//product-item")[:6] # Extracted 5 products

    products = []
    for card in product_cards:
        try:
            title = card.xpath(".//a[contains(@class, 'product-item-meta__title')]/text()")[0].strip()
            relative_url = card.xpath(".//a[contains(@class, 'product-item-meta__title')]/@href")[0]
            full_url = base_url + relative_url

            price = card.xpath(".//div[contains(@class,'price-list')]//span[contains(@class, 'price')]/text()")[1].strip()

            image_src = card.xpath(".//img[contains(@class, 'product-item__primary-image')]/@src")
            image_url = "https:" + image_src[0] if image_src else None
            
            size_chart=extract_size_chart_from_product_page(full_url)
            products.append({
                "product_title": title,
                "product_url": full_url,
                "price": price,
                "image_url": image_url,
                "size_chart":size_chart
            })

        except Exception as e:
            print(f"Error parsing product: {e}")
            continue

    return {
        "store_name": "freakins.com",
        "products": products
    }
    
