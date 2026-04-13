import re
import json

def extract_loto_data(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Line 311 is at index 310
    line = lines[310]
    
    # Try to find the JSON part
    match = re.search(r'const lotoData = (\[.*\]);', line)
    if match:
        json_str = match.group(1)
        data = json.loads(json_str)
        return data
    else:
        # Fallback search in case line numbers shifted slightly
        for l in lines:
            if 'const lotoData =' in l:
                match = re.search(r'const lotoData = (\[.*\]);', l)
                if match:
                    json_str = match.group(1)
                    data = json.loads(json_str)
                    return data
    return None

data = extract_loto_data('index.html')
if data:
    with open('lotoData.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully extracted {len(data)} entries.")
else:
    print("Failed to extract lotoData")
