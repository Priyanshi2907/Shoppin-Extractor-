import requests
from bs4 import BeautifulSoup
import time
import re
import ast
import unicodedata
from requests.exceptions import RequestException


BASE_URL = "https://www.westside.com"
COLLECTION_URL = f"{BASE_URL}/collections/view-all-western-wear-for-women"

# Rate Limit Handling Retries and backoff seamlessly
def fetch_with_retries(url, retries=3, backoff=1):
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response
        except RequestException as e:
            print(f"[Retry {attempt+1}] Error: {e}")
            time.sleep(backoff * (2 ** attempt))
    raise Exception(f"Failed to fetch {url} after {retries} retries.")

def extract_size_chart(product_url):
    try:
        response = fetch_with_retries(product_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        table = soup.find("table")
        if not table:
            return None

        # Extract headers
        headers = [th.get_text(strip=True) for th in table.find("thead").find_all("th")]

        rows_data = []
        for tr in table.find("tbody").find_all("tr"):
            cells = tr.find_all("td")
            row = []

            for td in cells:
                # Prefer the "default" span if available
                default_span = td.find("span", class_="default")
                value = default_span.get_text(strip=True) if default_span else ""
                row.append(value)

            # Only add rows with at least one value
            if any(row):
                row_dict = dict(zip(headers, row))  # Zip only as many headers as exist
                rows_data.append(row_dict)

        return {
            "headers": headers,
            "rows": rows_data
        } if rows_data else None

    except Exception as e:
        print(f"⚠️ Error extracting size chart from {product_url}: {e}")
        return None

def scrape_westside():
    response = fetch_with_retries(COLLECTION_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch Westside collection: {response.status_code}")

    soup = BeautifulSoup(response.text, "html.parser")

    # Find the script tag containing gsf_conversion_data to extract the data
    script_tag = soup.find("script", string=re.compile(r"gsf_conversion_data\s*="))
    if not script_tag:
        raise Exception("Could not find the gsf_conversion_data script.")

    # Extract just the product_data array from the script
    match = re.search(r"product_data\s*:\s*(\[[\s\S]+?\])", script_tag.string)
    if not match:
        raise Exception("product_data not found in script.")

    product_data_raw = match.group(1)

    # Quote unquoted keys using regex for ast.literal_eval
    product_data_fixed = re.sub(r"(\b\w+\b)\s*:", r"'\1':", product_data_raw)

    # Convert to Python list of dicts
    product_data = ast.literal_eval(product_data_fixed)

    # Extract relevant fields
    products = []
    for item in product_data:
        # To extract Url
        try:        # Error handling
            name=item.get("name","")
        except KeyError:
            print("Missing Product name,Skiping")
            continue
        
        sku=item.get("sku","")
        trimmed_sku = sku[:-3] if len(sku) > 3 else sku
        url=makeUrl(name)
        productUrl=f"{BASE_URL}/products/{url}-{trimmed_sku}"  #Created Product Url by defining Function makeUrl
        
        size_chart=extract_size_chart(productUrl)
        products.append({
            "product_title": item.get("name"),
            "brand": item.get("brand"),
            "sku": item.get("sku"),
            "Product Url" :productUrl,
            "variant": item.get("variant"),
            "price": f"₹ {item.get('price')}",
            "size_chart": size_chart
        })

    return {
        "store_name": "westside.com",
        "products": products
    }
    
def makeUrl(text):
    """
    Convert product name to Shopify handle: lowercase, hyphens, no punctuation.
    """
    text = unicodedata.normalize("NFKD", text)
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s]+", "-", text).strip("-")

