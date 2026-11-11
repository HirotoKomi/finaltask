import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from playwright.sync_api import sync_playwright

url = 'https://github.com/orgs/google/repositories'
DB_FILE = "google_github.db"

def to_int(text):
    text = text.strip().replace(",","").lower()
    if not text:
        return 0
    if text.endswith("k"):
        return int(float(text[:-1]) * 1000)
    return int(text)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False,slow_mo=1000)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_load_state()

    rows = page.locator("ul[data-listview-component='items-list'] > li")
    rows.first.wait_for()
    google = []
    
    for i in range(rows.count()):
        row = rows.nth(i)
        repository_name = row.locator("h4 a").first.inner_text().strip()

        language_loc = row.locator("span[class*='PrimaryLanguageName']")
        main_language = (
            language_loc.first.inner_text().strip()
            if language_loc.count() > 0
            else None
        )
        
        star_loc = row.locator("a[href$='/stargazers']")
        stars = (
            to_int(star_loc.first.inner_text())
            if star_loc.count()
            else 0
        )

        google.append((repository_name,main_language,stars))

    time.sleep(1)
    browser.close()

print("取得したリポジトリの数：",len(google))
print()

conn = sqlite3.connect(DB_FILE)
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS google (
    repository_name TEXT PRIMARY KEY,
    main_language TEXT,
    stars INTEGER
    );   
""")

cur.execute("DELETE from google")

cur.executemany("INSERT INTO google (repository_name,main_language,stars) VALUES (?,?,?);" ,google)
conn.commit()
print(f"{DB_FILE}に保存しました")

count = cur.execute(
    "SELECT count(*) FROM google").fetchone()[0]
print("保存された件数",count)

print("ーーーリポジトリ表示ーーー")

for row in cur.execute(
    "SELECT repository_name,main_language,stars FROM google LIMIT 5;"
):
    print(row)

conn.close()