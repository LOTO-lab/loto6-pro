import re
import os

filepath = r'c:\Users\Kentaro\Desktop\LOTO7\loto6_board_with_setball.html'

def final_fix():
    print(f"Reading {filepath}...")
    content = None
    # Try multiple encodings to handle SHIFT_JIS and UTF-8 mixed scenarios
    for enc in ['cp932', 'shift_jis', 'utf-8']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            print(f"Read success with {enc}")
            break
        except Exception:
            continue
    
    if not content:
        print("Failed to read file.")
        return

    # 1. Update Path to match Firebase Rules
    # Current code might have many variants, let's target the core updateVisitorCount block
    content = re.sub(
        r"const visitorRef = ref\(db, [`'].*?visitors.*?[`']\);",
        "const visitorRef = ref(db, 'stats/daily_visitors/count');",
        content
    )

    # 2. Add Visual Verification Marker (Blue border on stats card)
    # Target the stats card area
    content = content.replace(
        '.sidebar {',
        '.stat-verified { border: 3px solid #3b82f6 !important; position: relative; }\n        .sidebar {'
    )
    content = content.replace(
        'id="statVisitors"',
        'id="statVisitors" class="stat-verified"'
    )

    # 3. Update Title version for confirmation
    content = re.sub(
        r"<title>.*?</title>",
        "<title>LOTO6 分析プラットフォーム (vFinal-Fix)</title>",
        content
    )

    # Save the file cleanly
    with open(filepath, 'w', encoding='cp932', errors='ignore') as f:
        f.write(content)
    print("Final fix applied successfully.")

if __name__ == "__main__":
    final_fix()
