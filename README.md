# Shopify-Extractor
Shoppin 6B Assignment

## ⚙️ Setup Instructions

1. Clone the Repository

```bash
git clone https://github.com/your-username/shopify_size_chart_scraper.git
cd shopify_size_chart_scraper

2. Create a Virtual Environment (Optional but Recommended)

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install Required Dependencies

    pip install -r requirements.txt

    #Also Run  For size chart Extraction into Terminal
    playwright install

▶️ How to Run
Default Run (All Domains)
    python main.py

Custom Domain Selection
    To scrape a subset of supported domains, modify the list in main.py:
    -> store_list = ["westside.com", "freakins.com"]  # Add/remove domains as needed

📝 Output
After running, you'll find a file:

    aggregated_output.json

Example structure:

{
  "westside.com": {
    "store_name": "westside.com",
    "products": [
      {
        "product_title": "...",
        "size_chart": { ... }
      }
    ]
  },
  ...
}

## Instruction to run "Suqah.com, freakins.com"
1. Install dependecies from requirements.txt
2. Also install tesseract-ocr engine if not already:

Download: https://github.com/tesseract-ocr/tesseract

Direct Windows installer (recommended):
👉 https://github.com/UB-Mannheim/tesseract/wiki


After installing it:

Set the path (Only on Windows):
Add this in your script:

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' according to your system file path

Then run these 2 again
##

🔧 Requirements
* Python 3.7+
*Internet connection (for live scraping)

❓ FAQ
Q: The scraper doesn't find the size chart on some sites. Why?
A: Some websites load the size chart dynamically or use images. We handle some with Playwright or OCR.

Q: How do I add support for a new store?
A: Create a new file in the extractors/ folder and add the domain-function mapping in main.py.

🧪 Tested On
✅ westside.com

✅ littleboxindia.com

✅ suqah.com

✅ freakins.com
