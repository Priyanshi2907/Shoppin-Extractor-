from extractors.westside import scrape_westside
from extractors.freakins import scrape_freakins
from extractors.littleboxindia import scrape_littleboxindia
from extractors.suqah import scrape_suqah

import json

# Mapping of domain to function
SCRAPER_MAP = {
    "westside.com": scrape_westside,
    "freakins.com": scrape_freakins,
    "littleboxindia.com": scrape_littleboxindia,
    "suqah.com": scrape_suqah
}

def scrape_selected_stores(domains):
    aggregated_data = {}

    for domain in domains:
        scraper_func = SCRAPER_MAP.get(domain)
        if scraper_func:
            try:
                print(f"-> Scraping {domain} ...")
                data = scraper_func()
                aggregated_data[domain] = data
                print(f"✅ {domain} scraped successfully.")
            except Exception as e:
                print(f"❌ Failed to scrape {domain}: {e}")
        else:
            print(f"⚠️ No scraper function defined for: {domain}")

    # Save all data in one JSON file
    with open("final_output.json", "w", encoding="utf-8") as f:
        json.dump(aggregated_data, f, indent=2, ensure_ascii=False)
    print("📁 All data saved to aggregated_output.json")

if __name__ == "__main__":
    # Example usage
    store_list = ["westside.com", "littleboxindia.com", "suqah.com", "freakins.com"]

    scrape_selected_stores(store_list)
