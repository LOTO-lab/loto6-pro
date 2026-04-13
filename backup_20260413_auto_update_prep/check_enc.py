import os

file_path = r'c:\Users\Kentaro\Desktop\LOTO7\loto6_board_with_setball.html'

def try_read(enc):
    try:
        with open(file_path, 'r', encoding=enc) as f:
            f.read()
        print(f"Success with {enc}")
        return True
    except Exception as e:
        print(f"Failed with {enc}: {e}")
        return False

if not try_read('utf-8'):
    if not try_read('cp932'):
        try_read('utf-16')
