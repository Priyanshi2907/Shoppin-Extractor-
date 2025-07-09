from fastapi import FastAPI
from extractors.westside import scrape_westside
from extractors.freakins import scrape_freakins
from extractors.littleboxindia import scrape_littleboxindia
from extractors.suqah import scrape_suqah
import json
from fastapi import FastAPI, Query
from typing import List


app = FastAPI()

# Mapping of domain names to scraper functions
SCRAPERS = {
    "westside.com": scrape_westside,
    "freakins.com": scrape_freakins,
    "littleboxindia.com": scrape_littleboxindia,
    "suqah.com": scrape_suqah,
}

@app.get("/extract")
def extract_size_chart(stores: List[str] = Query(...)):
    output = {}
    for store in stores:
        func = SCRAPERS.get(store)
        if func:
            try:
                output[store] = func()
            except Exception as e:
                output[store] = {"error": str(e)}
        else:
            output[store] = {"error": "Unsupported store"}
    return output

# Endpoint to check service health
@app.get("/")
def index():
    return {"message": "Shopify Size Chart Scraper API is running."}
