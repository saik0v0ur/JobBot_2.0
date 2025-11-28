# main.py — 100% FINAL VERSION (November 2025 – works forever)
import os
import re
import requests
from playwright.sync_api import sync_playwright

TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
URL     = "https://airtable.com/embed/app17F0kkWQZhC6HB/shrOTtndhc6HSgnYb/tblp8wxvfYam5sD04?viewControls=on"

# Load companies.txt
companies = {}
with open("companies.txt") as f:
    for line in f:
        if "|" in line:
            name, tier = line.strip().split("|", 1)
            companies[name.strip().lower()] = tier.strip()

# Already sent
sent = set(open("sent_ids.txt").read().splitlines()) if os.path.exists("sent_ids.txt") else set()
new_sent = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_selector('div[data-rowid]', timeout=90000)

    rows = page.query_selector_all('div[data-rowid]')
    print(f"Found {len(rows)} rows")

    for row in rows:
        row_id = row.get_attribute("data-rowid")
        if row_id in sent:
            continue

        # JOB TITLE — columnindex 0 (you just proved it)
        title_cell = row.query_selector('div[data-columnindex="0"]')
        title = title_cell.inner_text().strip() if title_cell else "Untitled"

        # COMPANY — columnindex 5
        company_cell = row.query_selector('div[data-columnindex="5"]')
        company_full = company_cell.inner_text().strip() if company_cell else ""
        if not company_full:
            continue

        # APPLY LINK — columnindex 2 (green button)
        link = "No link"
        link_a = row.query_selector('div[data-columnindex="2"] a')
        if link_a:
            href = link_a.get_attribute("href")
            if href:
                link = href

        # YC detection
        yc_match = re.search(r'\(YC\s+(\w+\d+)\)', company_full, re.I)
        yc_tier = f"YC {yc_match.group(1).upper()}" if yc_match else None
        base = re.sub(r'\s*\(YC\s+\w+\d+\)\s*', '', company_full, flags=re.I).strip().lower()

        tier = companies.get(base) or yc_tier
        if tier:
            msg = f"New Job: {title}\nCompany: {company_full}\nTier: {tier}\nLink: {link}"
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data={"chat_id": CHAT_ID, "text": msg, "disable_web_page_preview": True}
            )
            new_sent.append(row_id)
            print(f"ALERT → {company_full} | {title}")

    browser.close()

if new_sent:
    with open("sent_ids.txt", "a") as f:
        f.write("\n".join(new_sent) + "\n")
    print(f"Sent {len(new_sent)} alerts")
else:
    print("No new jobs")