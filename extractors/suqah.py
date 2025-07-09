import requests
from lxml import html
import time
from requests.exceptions import RequestException
from playwright.sync_api import sync_playwright,TimeoutError as PlaywrightTimeoutError

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

def extract_suqah_size_chart(product_url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # Use headless=False for debugging
        page = browser.new_page()
        try:
            print("extracting product....")
            page.goto(product_url, timeout=100000)
            
            # Wait explicitly for size chart div
            page.wait_for_selector("div.goodsc-cart__timer-title table", timeout=8000)

            content = page.content()
            tree = html.fromstring(content)

            # Extract table
            table = tree.xpath("//div[contains(@class, 'goodsc-cart__timer-title')]//table")[0]
            rows = table.xpath(".//tr")

            headers = [td.text_content().strip() for td in rows[0].xpath(".//td")]
            if not headers[0]: headers[0] = "Size"

            data = []
            for row in rows[1:]:
                values = [td.text_content().strip() for td in row.xpath(".//td")]
                if len(values) == len(headers):
                    data.append(dict(zip(headers, values)))

            return {
                "headers": headers,
                "rows": data
            }

        except PlaywrightTimeoutError:
            print("⚠️ Timeout: Size chart table not found.")
            return None
        except Exception as e:
            print(f"⚠️ Error: {e}")
            return None
        finally:
            browser.close()



def scrape_suqah():
    url = "https://www.suqah.com/collections/padded-bodysuits"
    base_url = "https://www.suqah.com"

    response = fetch_with_retries(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {response.status_code}")
        
    tree = html.fromstring(response.content)
    # Select all product blocks
    product_cards = tree.xpath("//li[@class='grid__item']")

    products = []
    for card in product_cards:
        try:                    # Implemented Error Handling
            title = card.xpath(".//h3[contains(@class,'card__heading')]/a/text()")
            if not title:
                continue
            title = title[0].strip()

            relative_url = card.xpath(".//h3[contains(@class,'card__heading')]/a/@href")
            if not relative_url:
                continue
            full_url = base_url + relative_url[0]

            image_src = card.xpath(".//div[contains(@class,'card__media')]//img[1]/@src")
            if not image_src:
                continue
            image_url = "https:" + image_src[0] if image_src[0].startswith("//") else image_src[0]

            price_texts = card.xpath(".//div[contains(@class,'price')]//span[contains(@class,'price-item--sale')]/text()")
            if not price_texts:
                price_texts = card.xpath(".//div[contains(@class,'price')]//span[contains(@class,'price-item--regular')]/text()")
            price = price_texts[0].strip() if price_texts else "N/A"
            
            size_chart=extract_suqah_size_chart(full_url)
            products.append({
                "product_title": title,
                "product_url": full_url,
                "price": price,
                "image_url": image_url,
                "size_chart":size_chart
            })

        except Exception as e:
            # Skip and log silently or with minimal message
            print(f"Skipped a product due to missing fields.")
            continue

    return {
        "store_name": "suqah.com",
        "products": products
    }
    
    