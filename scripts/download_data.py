"""Download the davidcariboo/player-scores dataset from Kaggle into data/raw/."""

import shutil
from pathlib import Path

import kagglehub

DATASET = "davidcariboo/player-scores"
DEST_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def main() -> None:
    DEST_DIR.mkdir(parents=True, exist_ok=True)

    cache_path = Path(kagglehub.dataset_download(DATASET))
    print(f"Datasett lastet ned til cache: {cache_path}")

    csv_files = list(cache_path.glob("*.csv"))
    if not csv_files:
        raise RuntimeError(f"Fant ingen CSV-filer i {cache_path}")

    for csv_file in csv_files:
        target = DEST_DIR / csv_file.name
        shutil.copy2(csv_file, target)
        print(f"Kopiert: {csv_file.name} -> {target}")

    print(f"Ferdig. {len(csv_files)} fil(er) i {DEST_DIR}")


if __name__ == "__main__":
    main()
