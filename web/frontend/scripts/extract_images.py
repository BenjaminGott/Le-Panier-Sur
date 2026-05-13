"""Decode champignons_images.csv (base64) into static/img/{slug}.jpg + meta json.

Run from web/frontend/ :
    python scripts/extract_images.py
"""

from __future__ import annotations

import base64
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parents[1]
SRC_CSV = PROJECT_ROOT / "data" / "clean_web" / "champignons_images.csv"
OUT_IMG = ROOT / "static" / "img"
OUT_META = ROOT / "static" / "data" / "champignons_meta.json"


def slugify(name: str) -> str:
    norm = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    norm = norm.lower()
    norm = re.sub(r"[^a-z0-9]+", "-", norm).strip("-")
    return norm or "inconnu"


def main() -> int:
    if not SRC_CSV.exists():
        print(f"[!] CSV not found: {SRC_CSV}", file=sys.stderr)
        return 1

    OUT_IMG.mkdir(parents=True, exist_ok=True)
    OUT_META.parent.mkdir(parents=True, exist_ok=True)

    csv.field_size_limit(2**27)

    meta: list[dict] = []
    seen: set[str] = set()

    with SRC_CSV.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            nom = (row.get("nom") or "").strip()
            if not nom:
                continue
            slug = slugify(nom)
            base = slug
            i = 2
            while slug in seen:
                slug = f"{base}-{i}"
                i += 1
            seen.add(slug)

            payload = (row.get("image_base64") or "").strip()
            ext = "jpg"
            if payload.startswith("data:"):
                head, _, b64 = payload.partition(",")
                if "image/png" in head:
                    ext = "png"
                elif "image/webp" in head:
                    ext = "webp"
                payload = b64

            img_path = OUT_IMG / f"{slug}.{ext}"
            try:
                data = base64.b64decode(payload, validate=False)
                img_path.write_bytes(data)
                meta_entry = {
                    "nom": nom,
                    "slug": slug,
                    "image": f"/img/{slug}.{ext}",
                }
            except Exception as exc:  # noqa: BLE001
                print(f"[skip] {nom}: {exc}", file=sys.stderr)
                meta_entry = {"nom": nom, "slug": slug, "image": ""}

            meta.append(meta_entry)

    OUT_META.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Also copy the clean CSV next to the meta file
    clean_csv = PROJECT_ROOT / "data" / "clean_web" / "champignons_clean.csv"
    if clean_csv.exists():
        dst = ROOT / "static" / "data" / "champignons_clean.csv"
        dst.write_bytes(clean_csv.read_bytes())
        print(f"[ok] copied {clean_csv.name} -> {dst.relative_to(ROOT)}")

    print(f"[ok] {len(meta)} entries -> {OUT_META.relative_to(ROOT)}")
    print(f"[ok] images written to {OUT_IMG.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
