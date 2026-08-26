"""Rank the players that pass the obscurity filter (see
obskur-spiller-dataset-plan.md) and write data/processed/obscurity_ranking.csv
-- the single source-of-truth file the site's JSON is generated from.

Score = average of two inverted percentile ranks, both within the population
that passes the filter:
  - obscurity_minutes: 1 - percentile_rank(total_minutes_top5)   (fewer minutes -> higher)
  - obscurity_value:   1 - percentile_rank(peak_market_value_eur) (lower peak value -> higher)

Score is in [0, 1]; 1.0 would mean lowest minutes AND lowest peak value in the
whole eligible pool.
"""

from pathlib import Path

import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"
MIN_APPEARANCES = 30  # utelukker rene cameo-spillere (f.eks. 1 kamp/1 minutt) fra rangeringen

LEAGUE_NAMES = {
    "GB1": "Premier League",
    "ES1": "La Liga",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
}


def main() -> None:
    summary = pd.read_csv(PROCESSED_DIR / "player_career_summary.csv")
    players = pd.read_csv(PROCESSED_DIR / "players.csv")
    seasons = pd.read_csv(PROCESSED_DIR / "player_seasons.csv")

    eligible = summary[
        summary["passes_obscurity_filter"] & (summary["total_appearances"] >= MIN_APPEARANCES)
    ].copy()
    print(
        f"Rangerer {len(eligible):,} spillere som passerer filteret "
        f"og har >= {MIN_APPEARANCES} kamper".replace(",", " ")
    )

    eligible["obscurity_minutes"] = 1 - eligible["total_minutes_top5"].rank(pct=True)
    eligible["obscurity_value"] = 1 - eligible["peak_market_value_eur"].rank(pct=True)
    eligible["obscurity_score"] = (
        eligible["obscurity_minutes"] + eligible["obscurity_value"]
    ) / 2

    # Klubb(er)/liga(er) spilt for i studieperioden (2012/13-2019/20, topp 5-ligaer),
    # i kronologisk rekkefølge (sesong), duplikater fjernet men rekkefølge bevart.
    seasons_sorted = seasons.sort_values(["player_id", "season"])
    clubs_by_player = seasons_sorted.groupby("player_id")["club"].agg(
        lambda s: "; ".join(dict.fromkeys(s))
    )
    leagues_by_player = seasons_sorted.groupby("player_id")["league"].agg(
        lambda s: "; ".join(dict.fromkeys(LEAGUE_NAMES.get(x, x) for x in s))
    )

    ranked = eligible.merge(players, on="player_id", how="left")
    ranked = ranked.merge(clubs_by_player.rename("clubs"), on="player_id", how="left")
    ranked = ranked.merge(leagues_by_player.rename("leagues"), on="player_id", how="left")
    ranked = ranked.sort_values("obscurity_score", ascending=False).reset_index(drop=True)
    ranked.insert(0, "rank", ranked.index + 1)

    out_cols = [
        "rank",
        "player_id",
        "name",
        "clubs",
        "leagues",
        "nationality",
        "primary_position",
        "total_minutes_top5",
        "total_appearances",
        "peak_market_value_eur",
        "obscurity_score",
    ]
    ranked_out = ranked[out_cols]
    ranked_out.to_csv(PROCESSED_DIR / "obscurity_ranking.csv", index=False)
    print(f"Skrev {len(ranked_out):,} spillere til obscurity_ranking.csv".replace(",", " "))

    pd.set_option("display.max_colwidth", 40)
    pd.set_option("display.width", 160)
    print("\nTopp 10:\n")
    print(ranked_out.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
