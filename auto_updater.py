import requests
from bs4 import BeautifulSoup
import csv
import re
import os
import json
import urllib3

# 警告の抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ファイルパスの設定
CSV_PATH = "loto6_data_with_setball.csv"
HTML_PATH = "index.html"
# 最新結果が一番上にくるトップページを使用
TARGET_URL = "http://sougaku.com/loto6/"

def scrape_latest_result():
    print(f"Scraping latest result from {TARGET_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15, verify=False)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            print(f"Failed to fetch data. Status code: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 見出し（h3）を探す
        h3_title = soup.find("h3", string=re.compile("ロト６抽選結果速報"))
        if not h3_title:
            # 見つからない場合はh3タグを全スキャン（属性が含まれている場合があるため）
            for h3 in soup.find_all("h3"):
                if "ロト６抽選結果速報" in h3.get_text():
                    h3_title = h3
                    break
        
        if not h3_title:
            print("Target section header (h3) not found.")
            return None
        
        # 2. 回号・日付・セット球が含まれるテーブル (sokuho_tb1)
        info_table = h3_title.find_next("table")
        info_tds = [td.get_text().strip() for td in info_table.find_all("td")]
        # [0]:回号(第2092回), [1]:抽選日(2026年04月09日(木)), [2]:実績額, [3]:セット球(A)
        round_id = re.search(r"(\d+)", info_tds[0]).group(1)
        date_match = re.search(r"(\d{4})年(\d{2})月(\d{2})日", info_tds[1])
        date_str = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
        set_ball = info_tds[3]
        
        # 3. 当選番号が含まれるテーブル (sokuho_tb2)
        # 本数字の行を探す
        num_table = info_table.find_next("table")
        # 3行目に数字のみの行がある (08 13 27 36 37 43   03)
        num_rows = num_table.find_all("tr")
        data_tds = [td.get_text().strip() for td in num_rows[-1].find_all("td")]
        
        # 本数字 6個
        win_nums = [int(n) for n in data_tds[:6]]
        # ボーナス数字 (最後のtd)
        bonus_num = int(data_tds[-1])
        
        result = {
            "id": round_id,
            "date": date_str,
            "nums": win_nums,
            "bonus": bonus_num,
            "set_ball": set_ball
        }
        
        print(f"Scraped Result: 第{round_id}回 ({date_str}) nums:{win_nums} bonus:{bonus_num} set:{set_ball}")
        return result

    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def update_csv(latest):
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return False
    
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = list(csv.reader(f))
        rows = reader[1:]
    
    last_round_id = rows[-1][0] if rows else "0"
    
    if int(latest["id"]) <= int(last_round_id):
        print(f"No new data. Current CSV latest: {last_round_id}, Scraped: {latest['id']}")
        return False
    
    # 21列フォーマット
    new_row = [
        latest["id"], latest["date"],
        latest["nums"][0], latest["nums"][1], latest["nums"][2],
        latest["nums"][3], latest["nums"][4], latest["nums"][5],
        latest["bonus"],
        "0", "0", "0", "0", "0",
        "0", "0", "0", "0", "0",
        "0",
        latest["set_ball"]
    ]
    
    with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(new_row)
    
    print(f"Updated CSV with Round {latest['id']}")
    return True

def update_html():
    data = []
    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if not row: continue
            data.append({
                "id": f"第{row[0]}回",
                "date": row[1],
                "nums": [int(row[i]) for i in range(2, 8)],
                "bonus": int(row[8]),
                "set_ball": row[20]
            })
    
    data.reverse()
    
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    json_data = json.dumps(data, ensure_ascii=False, indent=4)
    new_content = re.sub(
        r"const lotoData = \[.*?\];",
        f"const lotoData = {json_data};",
        content,
        flags=re.DOTALL
    )
    
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"Updated {HTML_PATH} with {len(data)} entries.")

if __name__ == "__main__":
    latest = scrape_latest_result()
    if latest:
        is_new = update_csv(latest)
        update_html()
        if is_new:
            print("Successfully updated both CSV and HTML.")
        else:
            print("HTML rewritten with current data. Ready for tonight.")
