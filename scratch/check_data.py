import os

raw_file = 'lotoData_raw.txt'
if os.path.exists(raw_file):
    with open(raw_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Length: {len(content)}")
    print(f"Start: {content[:100]}")
    print(f"End: {content[-100:]}")
else:
    print("File not found")
