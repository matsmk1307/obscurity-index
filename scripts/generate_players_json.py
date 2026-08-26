"""Convert data/processed/obscurity_ranking.csv to JSON for the static site.

Writes two identical copies:
  - data/site/players.json   canonical processed-data output (matches the
                              data/processed/ -> data/site/ pipeline convention)
  - docs/data/players.json   the copy actually served by GitHub Pages -- Pages
                              only publishes files under docs/, so the site's
                              fetch() must point here, not at data/site/.
"""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SITE_DATA_DIR = ROOT / "data" / "site"
DOCS_DATA_DIR = ROOT / "docs" / "data"


def main() -> None:
    df = pd.read_csv(ROOT / "data" / "processed" / "obscurity_ranking.csv")
    df = df.sort_values("obscurity_score", ascending=False)
    df["nationality"] = df["nationality"].fillna("Ukjent")
    df["clubs"] = df["clubs"].fillna("Ukjent")
    df["leagues"] = df["leagues"].fillna("Ukjent")

    records = df.to_dict(orient="records")
    payload = json.dumps(records, ensure_ascii=False, indent=2)

    for out_dir in (SITE_DATA_DIR, DOCS_DATA_DIR):
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "players.json").write_text(payload, encoding="utf-8")
        print(f"Skrev {len(records)} spillere til {out_dir / 'players.json'}")


if __name__ == "__main__":
    main()
