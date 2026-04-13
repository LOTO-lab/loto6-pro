import csv
import os

CSV_PATH = r"c:\Users\Kentaro\Desktop\LOTO7\loto6_data_with_setball.csv"

def check_gaps():
    ids = []
    malformed = []
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        for i, row in enumerate(reader, start=2):
            if not row: continue
            if not row[0].isdigit(): continue
            
            draw_id = int(row[0])
            ids.append(draw_id)
            
            if len(row) < 21:
                malformed.append((draw_id, len(row), row))
                
    ids.sort()
    all_expected = set(range(ids[0], ids[-1] + 1))
    missing = sorted(list(all_expected - set(ids)))
    
    print(f"Total IDs found: {len(ids)}")
    print(f"ID Range: {ids[0]} - {ids[-1]}")
    print(f"Missing IDs (Gaps): {missing}")
    print(f"Number of malformed rows (cols < 21): {len(malformed)}")
    for m in malformed:
        print(f"  ID {m[0]}: {m[1]} columns")

if __name__ == "__main__":
    check_gaps()
