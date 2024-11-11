import re
import sys

arg = sys.argv[1]
with open(arg, "rt") as f:
    txt = f.readlines()
for s in arg:
    if "mapped" in s:
        break
try:
    res = re.findall("\(\d+\.", s)
    res = int(res)
finally:
    print("BAD")
if res >= 90:
    print("GOOD")
else:
    print("BAD")
