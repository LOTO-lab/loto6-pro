import csv
import os

CSV_PATH = r"c:\Users\Kentaro\Desktop\LOTO7\loto6_data_with_setball.csv"
BACKUP_PATH = r"c:\Users\Kentaro\Desktop\LOTO7\loto6_data_with_setball.csv.bak"

def fix_csv():
    # Make backup
    if not os.path.exists(BACKUP_PATH):
        import shutil
        shutil.copy2(CSV_PATH, BACKUP_PATH)
        print(f"Backup created at {BACKUP_PATH}")

    rows = []
    fixed_count = 0
    with open(CSV_PATH, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        header = next(reader)
        rows.append(header)
        for row in reader:
            if not row:
                rows.append(row)
                continue
            
            # IDs 2086-2089 usually have 10 columns
            if row[0].isdigit() and 2086 <= int(row[0]) <= 2089 and len(row) == 10:
                draw_id = row[0]
                date = row[1]
                numbers = row[2:8]
                bonus = row[8]
                set_ball = row[9]
                
                # Expand to 21 columns
                # 0:ID, 1:Date, 2-7:Nums, 8:Bonus
                # 9-13: Winners(5), 14-18: Amounts(5), 19: Carryover, 20: SetBall
                new_row = [draw_id, date] + numbers + [bonus] + ["0"]*5 + ["0"]*5 + ["0"] + [set_ball]
                rows.append(new_row)
                fixed_count += 1
                print(f"Fixed Draw {draw_id}: {len(new_row)} columns")
            else:
                rows.append(row)

    if fixed_count > 0:
        with open(CSV_PATH, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
        print(f"Successfully updated {CSV_PATH}. Rows fixed: {fixed_count}")
    else:
        print("No malformed rows found for 2086-2089.")

if __name__ == "__main__":
    fix_csv()
