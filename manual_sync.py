import csv
import json
import os
import re
import datetime

# 設定
CSV_PATH = "loto6_data_with_setball.csv"
JSON_DATA_PATH = "lotoData.json"
JS_DATA_PATH = "loto6_data.js"
JST = datetime.timezone(datetime.timedelta(hours=9))

def now_jst():
    return datetime.datetime.now(JST)

def update_local_files():
    try:
        data = []
        with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader) # header
            for row in reader:
                if not row or len(row) < 21: continue
                # 文字化け防止のため Unicode エスケープを使用
                # 第 = \u7b2c, 回 = \u56de
                round_label = f"\u7b2c{row[0]}\u56de"
                data.append({
                    "id": round_label, "date": row[1],
                    "numbers": [int(row[i]) for i in range(2, 8)],
                    "bonus": int(row[8]), "carryover": row[19], "set_ball": row[20],
                    "sum": sum([int(row[i]) for i in range(2, 8)])
                })
        data.reverse() # 最新が上
        with open(JSON_DATA_PATH, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        with open(JS_DATA_PATH, "w", encoding="utf-8-sig") as f:
            f.write(f"const lotoData = {json.dumps(data, ensure_ascii=False)};")
        print("Local JSON/JS files updated.")
        return data
    except Exception as e:
        print(f"File Update Error: {e}")
        return None

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
        now = now_jst()
        version_str = now.strftime("%Y%m%d-%H%M")
        content = re.sub(r"<!-- Version: \d{8}-\d{4} -->", f"<!-- Version: {version_str} -->", content)
        
        # 最終更新日の表示を更新 (YYYY/MM/DD)
        date_str = now.strftime("%Y/%m/%d")
        content = re.sub(r'<span id="update-date".*?>最終更新日: .*?</span>', f'<span id="update-date" style="margin-left: auto; font-size: 13px; color: #64748b; font-weight: 600;">最終更新日: {date_str}</span>', content)

        # setBallStats オブジェクトの更新
        stats_json = json.dumps(set_ball_stats, ensure_ascii=False)
        content = re.sub(r"const setBallStats = \{.*?\};", f"const setBallStats = {stats_json};", content, flags=re.DOTALL)
        
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("index.html patched.")
        return True
    except Exception as e:
        print(f"Error patching index.html: {e}")
        return False

if __name__ == "__main__":
    data = update_local_files()
    if data:
        sb_stats = calculate_set_ball_stats(data)
        patch_index_html(sb_stats)
