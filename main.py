import requests
import os
import re
from bs4 import BeautifulSoup

# === CONFIG ===
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TELEGRAM_CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
URL = 'https://airtable.com/embed/app17F0kkWQZhC6HB/shrOTtndhc6HSgnYb/tblp8wxvfYam5sD04?viewControls=on'

# === 1. Scrape the embed page to extract the real data endpoint ===
response = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
response.raise_for_status()
soup = BeautifulSoup(response.text, 'html.parser')

urlWithParams = None
for script in soup.find_all('script', attrs={'nonce': True}):
    if script.string and 'urlWithParams' in script.string:
        match = re.search(r'urlWithParams: "([^"]+)"', script.string)
        if match:
            urlWithParams = match.group(1)
            break

if not urlWithParams:
    raise ValueError("Could not find data URL in page source")

data_url = 'https://airtable.com' + urlWithParams

# === 2. Load your tracked companies ===
companies = {}
with open('companies.txt', 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line and '|' in line:
            company, tier = line.split('|', 1)
            companies[company.strip().lower()] = tier.strip()

# === 3. Load already-sent record IDs ===
sent_ids = set()
if os.path.exists('sent_ids.txt'):
    with open('sent_ids.txt', 'r', encoding='utf-8') as f:
        sent_ids = {line.strip() for line in f if line.strip()}

# === 4. Fetch all records (with pagination) ===
headers = {
    'User-Agent': 'Mozilla/5.0',
    'X-Requested-With': 'XMLHttpRequest',
    'x-user-locale': 'en',
    'x-time-zone': 'UTC',
}
records = []
offset = None
while True:
    url = data_url + (f'&offset={offset}' if offset else '')
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    records.extend(data['data']['rows'])
    offset = data['data'].get('offset')
    if not offset:
        break

# === 5. Process records ===
new_sent = []
for record in records:
    rec_id = record['id']
    fields = record.get('fields', {})
    company_full = fields.get('Company', '').strip()
    if not company_full or rec_id in sent_ids:
        continue

    company_lower = company_full.lower()

    # Detect YC pattern and extract season (e.g., "TraceRoot.AI (YC S25)" → "YC S25")
    yc_match = re.search(r'\(yc\s+(\w+\d+)\)', company_lower)
    yc_tier = f"YC {yc_match.group(1).upper()}" if yc_match else None

    # Remove YC part for matching against companies.txt
    base_company = re.sub(r'\s*\(yc\s+\w+\d+\)\s*', '', company_lower).strip()

    # Decide if we should send alert
    tier = companies.get(base_company)  # First priority: exact match in list
    if not tier and yc_tier:            # Second priority: any YC company
        tier = yc_tier

    if tier:
        job_title = fields.get('Job Title', 'N/A')
        link = fields.get('Link', 'N/A')

        message = f"New Job: {job_title}\nCompany: {company_full}\nTier: {tier}\nLink: {link}"

        tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'disable_web_page_preview': True}
        requests.post(tg_url, data=payload).raise_for_status()

        new_sent.append(rec_id)

# === 6. Save new sent IDs ===
if new_sent:
    with open('sent_ids.txt', 'a', encoding='utf-8') as f:
        for rid in new_sent:
            f.write(rid + '\n')