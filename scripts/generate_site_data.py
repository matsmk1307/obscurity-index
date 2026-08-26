"""Turn data/processed/obscurity_ranking_top50.csv into site/data.js so the
static site can read it with a plain <script> tag (no server/CORS needed --
works straight from a double-clicked index.html, and also when hosted)."""

import json
from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
SITE_DIR = Path(__file__).resolve().parent.parent / "site"


def main() -> None:
    df = pd.read_csv(PROCESSED_DIR / "obscurity_ranking_top50.csv")
    df["nationality"] = df["nationality"].fillna("Ukjent")
    records = df.to_dict(orient="records")

    js = "// Generert av scripts/generate_site_data.py -- ikke rediger for hånd\n"
    js += "const PLAYERS = " + json.dumps(records, ensure_ascii=False, indent=2) + ";\n"

    SITE_DIR.mkdir(parents=True, exist_ok=True)
    (SITE_DIR / "data.js").write_text(js, encoding="utf-8")
    print(f"Skrev {len(records)} spillere til {SITE_DIR / 'data.js'}")


if __name__ == "__main__":
    main()
