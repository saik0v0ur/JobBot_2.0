# printer.py — THE ONE THAT ACTUALLY WORKS (flat grid version – November 28 2025)
from playwright.sync_api import sync_playwright

URL = "https://airtable.com/embed/app17F0kkWQZhC6HB/shrOTtndhc6HSgnYb/tblp8wxvfYam5sD04?viewControls=on"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Keep False so you can watch
    page = browser.new_page()
    page.goto(URL)
    
    page.wait_for_selector('div[data-rowid]', timeout=90000)
    # Force everything to load
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(6000)

    rows = page.query_selector_all('div[data-rowid]')
    print(f"\nFOUND {len(rows)} ROWS – PRINTING FIRST 12 WITH ALL COLUMNS\n")
    print("="*150)

    for i, row in enumerate(rows[:12], 1):
        print(f"\nROW {i:2} | RECORD ID: {row.get_attribute('data-rowid')}")
        print("-"*150)
        
        cells = row.query_selector_all('div[data-columnindex]')
        for cell in cells:
            idx = cell.get_attribute("data-columnindex")
            fid = cell.get_attribute("data-columnid") or "?"
            text = cell.inner_text(separator=" ", timeout=1000).strip()
            link = cell.query_selector("a")
            link_url = link.get_attribute("href") if link else None
            
            print(f"  Col {idx.rjust(2)} | Field ID …{fid[-10:]:10} | {text[:80]:80}", end="")
            if link_url:
                print(f" → {link_url}")
            else:
                print("")
        print("-"*150)

    input("\nPress Enter to close the browser...")
    browser.close()