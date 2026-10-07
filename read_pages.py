"""Print a compact but complete range of extracted PDF pages (inclusive)."""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
path, start, end = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
text = (Path(__file__).parent / "paper_text" / path).read_text(encoding="utf-8")
pages = re.split(r"\[PAGE (\d+)\]\n", text)
for i in range(1, len(pages), 2):
    if start <= int(pages[i]) <= end:
        print("[PAGE", pages[i] + "]")
        print(re.sub(r"[ \t]+", " ", pages[i+1]))
