
import chardet

filepath = r'c:\Users\Kentaro\Desktop\LOTO7\loto6_board_with_setball.html'
with open(filepath, 'rb') as f:
    rawdata = f.read(10000)
    result = chardet.detect(rawdata)
    print(result)
