import requests
from bs4 import BeautifulSoup
import csv
import re
import os
import json
import time
import datetime
import urllib3

# 警告の抑制
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 設定
CSV_PATH = "loto6_data_with_setball.csv"
JSON_DATA_PATH = "lotoData.json"
JS_DATA_PATH = "loto6_data.js"
TARGET_URL = "http://sougaku.com/loto6/"
FIREBASE_BASE_URL = "https://loto6-analytics-default-rtdb.firebaseio.com"

def fetch_from_firebase(path):
    url = f"{FIREBASE_BASE_URL}/{path}.json"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Firebase read error ({path}): {e}")
    return None

def update_firebase(path, data, method="put"):
    url = f"{FIREBASE_BASE_URL}/{path}.json"
    try:
        if method == "put":
            response = requests.put(url, json=data, timeout=15)
        elif method == "patch":
            response = requests.patch(url, json=data, timeout=15)
        elif method == "delete":
            response = requests.delete(url, timeout=15)
            return response.status_code == 200
        
        if response.status_code == 200:
            return True
        else:
            print(f"Firebase update failed ({path}): {response.status_code}")
    except Exception as e:
        print(f"Firebase update error ({path}): {e}")
    return False

def scrape_latest_result():
    print(f"[{datetime.datetime.now()}] Scraping from {TARGET_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15, verify=False)
        response.encoding = 'utf-8'
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        h3_title = soup.find("h3", string=re.compile("ロト６抽選結果速報"))
        if not h3_title:
            for h3 in soup.find_all("h3"):
                if "ロト６抽選結果速報" in h3.get_text():
                    h3_title = h3
                    break
        if not h3_title: return None
        
        info_table = h3_title.find_next("table")
        info_tds = [td.get_text().strip() for td in info_table.find_all("td")]
        round_id = re.search(r"(\d+)", info_tds[0]).group(1)
        date_match = re.search(r"(\d{4})年(\d{2})月(\d{2})日", info_tds[1])
        date_str = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
        set_ball = info_tds[3]
        
        num_table = info_table.find_next("table")
        num_rows = num_table.find_all("tr")
        data_tds = [td.get_text().strip() for td in num_rows[-1].find_all("td")]
        win_nums = [int(n) for n in data_tds[:6]]
        bonus_num = int(data_tds[-1])
        
        carry_over = "0"
        all_tds = soup.find_all("td")
        for i, td in enumerate(all_tds):
            if "キャリーオーバー" in td.get_text():
                next_td = all_tds[i+1] if i+1 < len(all_tds) else None
                if next_td:
                    val = next_td.get_text().replace(",", "").replace("円", "").strip()
                    if val.isdigit(): carry_over = val
                    break

        return {
            "round": int(round_id),
            "date": date_str,
            "numbers": win_nums,
            "bonus": bonus_num,
            "set_ball": set_ball,
            "sum": sum(win_nums),
            "carryover": carry_over
        }
    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def calculate_site_prizes(draw_id, win_nums, bonus_num):
    print(f"Calculating prizes for Draw {draw_id}...")
    predictions = fetch_from_firebase(f"site_predictions/{draw_id}")
    prizes = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    if not predictions: return prizes
    
    win_set = set(win_nums)
    for push_id, pred in predictions.items():
        nums = pred.get('nums', [])
        if not nums: continue
        pred_set = set(nums)
        match_count = len(pred_set & win_set)
        has_bonus = bonus_num in pred_set
        if match_count == 6: prizes[1] += 1
        elif match_count == 5 and has_bonus: prizes[2] += 1
        elif match_count == 5: prizes[3] += 1
        elif match_count == 4: prizes[4] += 1
        elif match_count == 3: prizes[5] += 1
    return prizes

def update_local_files(result):
    try:
        if os.path.exists(CSV_PATH):
            rows = []
            with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
                reader = list(csv.reader(f))
                rows = reader[1:]
            last_round = int(rows[-1][0]) if rows else 0
            if result["round"] > last_round:
                new_row = [result["round"], result["date"]] + result["numbers"] + [result["bonus"]] + ["0"]*11 + [result["set_ball"]]
                with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as f:
                    csv.writer(f).writerow(new_row)
        
        data = []
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) < 21: continue
                data.append({
                    "id": f"第{row[0]}回", "date": row[1],
                    "numbers": [int(row[i]) for i in range(2, 8)],
                    "bonus": int(row[8]), "set_ball": row[20],
                    "sum": sum([int(row[i]) for i in range(2, 8)])
                })
        data.reverse()
        with open(JSON_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(JS_DATA_PATH, "w", encoding="utf-8") as f:
            f.write(f"const lotoData = {json.dumps(data, ensure_ascii=False)};")
        print("Local files updated.")
    except Exception as e: print(f"File Update Error: {e}")

def run_update_process():
    latest = scrape_latest_result()
    if not latest: return False
    
    # 既に当選データに prizes があるかチェック (完了済みの証)
    # ※push失敗時のリカバリのため、一時的に常に実行するようにガードをコメントアウトします
    # current_winners = fetch_from_firebase("stats/winners")
    # if current_winners and current_winners.get("round") == latest["round"] and "prizes" in current_winners and current_winners.get("status") != "updating":
    #     print(f"Round {latest['round']} is ALREADY updated.")
    #     return True

    # 更新中フラグ
    update_firebase("stats/winners", {"status": "updating"}, method="patch")
    
    # 照合
    prizes = calculate_site_prizes(latest["round"], latest["numbers"], latest["bonus"])
    latest["prizes"] = prizes
    latest["status"] = "success"
    latest["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Firebase反映
    if update_firebase("stats/winners", latest):
        update_local_files(latest)
        # 照合済みデータの削除
        update_firebase(f"site_predictions/{latest['round']}", None, method="delete")
        return True
    return False

if __name__ == "__main__":
    # GitHub Actions用に最大8回（4時間）のリトライ制限を追加
    MAX_RETRIES = 8
    RETRY_INTERVAL = 1800 # 30分
    
    print("=== LOTO6PRO Auto Updater (GitHub Actions Mode) ===")
    for i in range(MAX_RETRIES):
        print(f"\nAttempt {i+1}/{MAX_RETRIES}...")
        if run_update_process():
            print("Successfully finished update process.")
            exit(0) # 正常終了
        
        if i < MAX_RETRIES - 1:
            print(f"Data not ready. Waiting {RETRY_INTERVAL/60} minutes for next attempt...")
            time.sleep(RETRY_INTERVAL)
    
    print("Reached maximum retries. Exiting for now.")
    exit(0) # エラーにせず終了 (GitHub Actionsのステータスを正常に保つ)
