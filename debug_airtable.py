from playwright.sync_api import sync_playwright
import time

URL = "https://airtable.com/embed/app17F0kkWQZhC6HB/shrOTtndhc6HSgnYb/tblp8wxvfYam5sD04?viewControls=on"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)  # Watch it load
    page = browser.new_page()
    page.goto(URL)
    
    print("Page loading... Wait 60 seconds, then check terminal.")
    time.sleep(60)  # Give it full time to render
    
    # Print page title & key elements
    print("=== PAGE TITLE ===")
    print(page.title())
    
    print("\n=== ALL DIV CLASSES WITH 'RT-' (React-Table hints) ===")
    rt_elements = page.query_selector_all("div[class*='rt-']")
    for el in rt_elements[:10]:  # First 10 for brevity
        print(el.get_attribute("class"))
    
    print("\n=== SAMPLE ROW ELEMENTS (look for data-record-id) ===")
    rows = page.query_selector_all("div[data-record-id]")
    print(f"Found {len(rows)} rows with data-record-id")
    if rows:
        for row in rows[:2]:  # First 2 rows
            print(f"Row ID: {row.get_attribute('data-record-id')}")
            cells = row.query_selector_all("div[class*='rt-td']")
            print(f"  Cells: {len(cells)}")
            for cell in cells[:3]:
                print(f"    Cell text: {cell.inner_text().strip()[:50]}...")  # First 50 chars
    
    input("Press Enter to close browser...")  # Pause so you can inspect
    browser.close()