from pathlib import Path
import json
import fitz

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "paper_text"
OUT.mkdir(parents=True, exist_ok=True)
inventory = []
for path in sorted((ROOT.parent / "papers").glob("*.pdf")):
    with fitz.open(path) as document:
        pages = [page.get_text(sort=True) for page in document]
    (OUT / (path.stem + ".txt")).write_text(
        "\n\n".join(f"[PAGE {i+1}]\n{text}" for i, text in enumerate(pages)),
        encoding="utf-8",
    )
    inventory.append({
        "file": path.name,
        "pages": len(pages),
        "characters": sum(map(len, pages)),
        "sparse_pages": [i+1 for i, text in enumerate(pages) if len(text.strip()) < 80],
    })
(ROOT / "paper_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
print(json.dumps(inventory, indent=2))
print("TOTAL", len(inventory), "papers", sum(item["pages"] for item in inventory), "pages")
