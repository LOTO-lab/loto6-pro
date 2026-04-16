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
        response.encoding = response.apparent_encoding
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ロト6専用のエリアを特定
        main_content = soup.find("div", id="main") or soup.find("article") or soup
        h3_title = main_content.find("h3", string=re.compile(r"ロト６(抽選結果|当選番号)速報"))
        if not h3_title:
            for h3 in main_content.find_all("h3"):
                if "ロト６" in h3.get_text() and "速報" in h3.get_text():
                    h3_title = h3
                    break
        
        if not h3_title:
            print("Target H3 title not found.")
            return None
        
        # 回号と日付の取得 (H3または直後のテーブルから取得)
        round_match = re.search(r"第(\d+)回", h3_title.get_text())
        info_table = h3_title.find_next("table")
        
        if not round_match and info_table:
            round_match = re.search(r"第(\d+)回", info_table.get_text())
            
        if not round_match:
            print("Round ID (第XXX回) not found.")
            return None
            
        round_id = round_match.group(1)
        
        # 日付とセット球の取得
        date_str = ""
        set_ball = ""
        
        # テーブル全体のテキストから日付を探す
        table_text = info_table.get_text()
        date_match = re.search(r"(\d{4})年(\d{2})月(\d{2})日", table_text)
        if date_match:
            date_str = f"{date_match.group(1)}/{date_match.group(2)}/{date_match.group(3)}"
        
        # セット球を探す (テーブルのtdを順番にチェック)
        for td in info_table.find_all(["td", "th"]):
            t = td.get_text().strip()
            # セット球は通常 A-J の1文字、または "Aセット" のような形式
            if re.match(r"^[A-J](\u30bb\u30c3\u30c8)?$", t):
                set_ball = t[0]
                break
        
        # 当選番号の取得 (専用テーブルを探す)
        num_table = h3_title.find_next("table", class_="winning-numbers") or info_table.find_next("table")
        # 本数字(6個)とボーナスを取得
        win_nums = []
        bonus_num = None
        
        tds = num_table.find_all("td")
        raw_nums = []
        for td in tds:
            val = td.get_text().strip()
            if val.isdigit():
                raw_nums.append(int(val))
        
        if len(raw_nums) >= 7:
            # sougaku.comの構造: 本数字6個、その後にボーナス
            win_nums = sorted(raw_nums[:6])
            bonus_num = raw_nums[6]
        else:
            print(f"Numbers not complete: {raw_nums}")
            return None

        # キャリーオーバー
        carry_over = "0"
        carry_section = soup.find(string=re.compile("\u30ad\u30e3\u30ea\u30fc\u30aa\u30fc\u30d0\u30fc"))
        if carry_section:
            parent = carry_section.find_parent(["td", "tr", "div"])
            val_match = re.search(r"([\d,]+)\u5186", parent.get_text()) if parent else None
            if val_match:
                carry_over = val_match.group(1).replace(",", "")

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
        # UTF-8 with BOM (utf-8-sig) を使用してWindows環境での文字化けを防止
        if os.path.exists(CSV_PATH):
            rows = []
            with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
                reader = list(csv.reader(f))
                rows = reader[1:]
            last_round = int(rows[-1][0]) if rows else 0
            new_row = [result["round"], result["date"]] + result["numbers"] + [result["bonus"]] + ["0"]*11 + [result["set_ball"]]
            if result["round"] > last_round:
                with open(CSV_PATH, "a", encoding="utf-8-sig", newline="") as f:
                    csv.writer(f).writerow(new_row)
            elif result["round"] == last_round:
                # 既存の最終行を更新
                all_rows = []
                with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
                    all_rows = list(csv.reader(f))
                all_rows[-1] = new_row
                with open(CSV_PATH, "w", encoding="utf-8-sig", newline="") as f:
                    csv.writer(f).writerows(all_rows)
        
        data = []
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if len(row) < 21: continue
                # 文字化け防止のため Unicode エスケープを使用
                # 第 = \u7b2c, 回 = \u56de
                round_label = f"\u7b2c{row[0]}\u56de"
                data.append({
                    "id": round_label, "date": row[1],
                    "numbers": [int(row[i]) for i in range(2, 8)],
                    "bonus": int(row[8]), "set_ball": row[20],
                    "sum": sum([int(row[i]) for i in range(2, 8)])
                })
        data.reverse()
        with open(JSON_DATA_PATH, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(JS_DATA_PATH, "w", encoding="utf-8-sig") as f:
            f.write(f"const lotoData = {json.dumps(data, ensure_ascii=False)};")
        print("Local files updated (UTF-8-SIG).")
    except Exception as e: print(f"File Update Error: {e}")

def calculate_set_ball_stats(data):
    stats_map = {}
    balls = ['A','B','C','D','E','F','G','H','I','J']
    for b in balls:
        filtered = [d for d in data if d.get("set_ball") == b]
        total_count = len(filtered)
        if total_count == 0:
            stats_map[b] = []
            continue
        counts = {}
        for d in filtered:
            for n in d["numbers"]:
                counts[n] = counts.get(n, 0) + 1
        # 出現回数降順、数字昇順でソート
        sorted_counts = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        top5 = []
        for n, c in sorted_counts[:5]:
            top5.append({
                "n": n,
                "c": c,
                "p": round((c / total_count) * 100, 1) if total_count > 0 else 0
            })
        stats_map[b] = top5
    return stats_map

def patch_index_html(set_ball_stats):
    html_path = "index.html"
    if not os.path.exists(html_path): return False
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # バージョン情報の更新 (YYYYMMDD-HHMM)
        version_str = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        content = re.sub(r"<!-- Version: \d{8}-\d{4} -->", f"<!-- Version: {version_str} -->", content)
        
        # setBallStats オブジェクトの更新
        stats_json = json.dumps(set_ball_stats, ensure_ascii=False)
        content = re.sub(r"const setBallStats = \{.*?\};", f"const setBallStats = {stats_json};", content, flags=re.DOTALL)
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("index.html patched with latest stats and version.")
        return True
    except Exception as e:
        print(f"Error patching index.html: {e}")
        return False

def run_update_process():
    latest = scrape_latest_result()
    if not latest: return False
    
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
        
        # 統計データの再計算とHTMLパッチ
        # 最新のJSONを読み込み直して計算
        if os.path.exists(JSON_DATA_PATH):
            with open(JSON_DATA_PATH, "r", encoding="utf-8-sig") as f:
                full_data = json.load(f)
                sb_stats = calculate_set_ball_stats(full_data)
                patch_index_html(sb_stats)

        # 照合済みデータの削除
        update_firebase(f"site_predictions/{latest['round']}", None, method="delete")
        return True
    return False

if __name__ == "__main__":
    # GitHub Actions用に最大8回（4時間）のリトライ制限を追加
    MAX_RETRIES = 8
    RETRY_INTERVAL = 1800 # 30分
    
    print("=== LOTO6PRO Auto Updater (Full Sync Mode) ===")
    for i in range(MAX_RETRIES):
        print(f"\nAttempt {i+1}/{MAX_RETRIES}...")
        if run_update_process():
            print("Successfully finished update process.")
            exit(0) # 正常終了
        
        if i < MAX_RETRIES - 1:
            print(f"Data not ready. Waiting {RETRY_INTERVAL/60} minutes for next attempt...")
            time.sleep(RETRY_INTERVAL)
    
    print("Reached maximum retries. Exiting for now.")
    exit(0)
