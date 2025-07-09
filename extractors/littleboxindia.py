# freakins_xpath_scraper.py
import requests
from lxml import html
import time
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
import json
from playwright.sync_api import sync_playwright
import time
import asyncio
import sys
# Workaround for Windows subprocess issue
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
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


def extract_size_chart(product_url):
    print("Extrating Size Chart for LittleBoxindia.....") # can take some time due to playwright installment
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto(product_url, timeout=30000)
            page.wait_for_selector(".ks-table-wrapper", timeout=10000)

            # Extract table HTML
            table_html = page.inner_html(".ks-table-wrapper")
            browser.close()

            # Parse with BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(table_html, "html.parser")
            rows = soup.find_all("tr")

            headers = [td.get_text(strip=True) for td in rows[0].find_all("td")]

            size_rows = []
            for tr in rows[1:]:
                tds = tr.find_all("td")
                if len(tds) < 3:
                    continue

                euro = tds[0].get_text(strip=True)
                uk = tds[1].get_text(strip=True)
                foot_len = tds[2].get_text(strip=True)

                size_rows.append({
                    headers[0]: euro,
                    headers[1]: uk,
                    headers[2]: foot_len
                })

            return {
                "headers": headers,
                "rows": size_rows
            } if size_rows else None

        except Exception as e:
            print(f"[Playwright Error] {e}")
            browser.close()
            return None

def scrape_littleboxindia():
    url = "https://littleboxindia.com/collections/womens-footwear-new-arrivals"
    base_url = "https://littleboxindia.com"

    response = fetch_with_retries(url)
    if response.status_code != 200:
        raise Exception(f"Failed to load page: {response.status_code}")
        
    tree = html.fromstring(response.content)
    
    # Select all product blocks
    product_cards = tree.xpath("//div[@class='product-block']")[0:4] #Extracted 5 products

    products = []
    for card in product_cards:
        try:
            #Title
            title = card.xpath(".//div[contains(@class, 'product-block__title')]/text()")[0].strip()

            #Relative URL
            relative_url = card.xpath(".//a[contains(@class, 'product-link')]/@href")[0]
            full_url = base_url + relative_url
            
            #Image URL
            image_url = card.xpath(".//img[contains(@class, 'rimage__image')]/@src")[0]
            image_url = "https:" + image_url

            #Price
            price = card.xpath(".//span[contains(@class, 'product-price__amount')]/text()")[0].strip()

            size_chart=extract_size_chart(full_url)
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
        "store_name": "littleboxindia.com",
        "products": products
    }
    
    