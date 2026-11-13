import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from playwright.sync_api import sync_playwright
page_num = 1

DB_FILE = "google_github.db"

# スターの数表示を統一
def to_int(text):
    text = text.strip().replace(",","").lower()
    if not text:
        return 0
    if text.endswith("k"):
        return int(float(text[:-1]) * 1000)
    return int(text)

with sync_playwright() as p:
    
    google = []
    browser = p.chromium.launch(headless=False,slow_mo=1000)
    page = browser.new_page()
    
    while True:
        
        print(f"{page_num}ページを取得中…")

        # URLを変更して次のページに移動する
        page.goto(f"https://github.com/orgs/google/repositories?page={page_num}")
        page.wait_for_load_state()

        # time.sleep(1)だと「Too many requests」が表示されるので、time.sleep(3)に変更
        time.sleep(3)
        
        rows = page.locator("ul[data-listview-component='items-list'] > li")
             
        for i in range(rows.count()):
            row = rows.nth(i)
            repo_loc = row.locator("h4 a")

            if repo_loc.count() == 0:
                print(f"{page_num}ページでリポジトリが見つからない")
                print(f"row={i}")
                print(row.inner_html())
                break

            # リポジトリ名の取得
            repository_name = row.locator("h4 a").first.inner_text().strip()

            # 主要言語の取得
            language_loc = row.locator("span[class*='PrimaryLanguageName']")
            main_language = (
                language_loc.first.inner_text().strip()
                if language_loc.count() > 0
                else None
            )

            # スター数の取得
            star_loc = row.locator("a[href$='/stargazers']")
            stars = (
                to_int(star_loc.first.inner_text())
                if star_loc.count()
                else 0
            )

            google.append((repository_name,main_language,stars))
        repo_links = page.locator("h4 a")

        if repo_links.count() == 0:
            print("リポジトリがなくなったので終了")
            break
        page_num += 1
    print(len(google))
    browser.close()

print("取得したリポジトリの数：",len(google))

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

print("ーーーリポジトリ表示(上位５件)ーーー")

for row in cur.execute(
    "SELECT repository_name,main_language,stars FROM google LIMIT 5;"
):
    print(row)

conn.close()