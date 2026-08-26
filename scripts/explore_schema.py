"""Print schema info (columns, dtypes, row count, head) for key raw CSV files."""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
FILES = ["appearances.csv", "player_valuations.csv", "players.csv", "clubs.csv"]


def explore(path: Path) -> None:
    df = pd.read_csv(path, low_memory=False)

    print(f"\n{'=' * 80}")
    print(f"Fil: {path.name}")
    print(f"{'=' * 80}")
    print(f"Antall rader: {len(df)}")
    print("\nKolonner og datatyper:")
    print(df.dtypes)
    print("\nFørste 5 rader:")
    print(df.head())


def main() -> None:
    for filename in FILES:
        explore(RAW_DIR / filename)


if __name__ == "__main__":
    main()
