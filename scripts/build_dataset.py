"""Full obscurity-filter pipeline (see obskur-spiller-dataset-plan.md).

Reads data/raw/*.csv, applies the filtering logic verified manually in
scripts/filter_test.py against a hand-picked sample, and writes the three
output tables from the plan's pkt. 4 schema to data/processed/:

  - players.csv                basic info for every player who appeared in a
                                top-5 league during 2012/13-2019/20
  - player_seasons.csv         one row per player/season/club in that window
  - player_career_summary.csv  aggregated, used for the actual filtering
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "processed"

TOP5_LEAGUES = {"GB1", "ES1", "IT1", "L1", "FR1"}
PERIOD_START_SEASON = 2012  # 2012/13 -- appearances.csv has no data before 2012-07-03
PERIOD_END_SEASON = 2019  # 2019/20

MAX_MINUTES = 9_000  # ~100 kamper -- strammet inn fra 18 000 (se chat), 68 % passerte da

# Markedsverdi-terskel: liga-relativ percentil, ikke en fast EUR-sum. En flat
# terskel (testet: 7M) straffet Premier League uforholdsmessig hardt (PL-markedet
# er strukturelt dyrere) og ga Ligue 1 en kunstig høy "obskur-rate" (26,6 % mot
# PL sine 13,4 %, se chat). Percentilen regnes blant alle spillere med samme
# hovedliga (mest minutter i perioden), så "obskur på verdi" betyr det samme
# uansett hvilken liga du tilhører.
MARKET_VALUE_PERCENTILE_CUTOFF = 0.5  # under/lik median peak-verdi i egen hovedliga

# Topplag-liste fra obskur-spiller-dataset-plan.md, pkt. 3. Scope: all-time
# (hele karrieren, ikke bare studieperioden) -- se begrunnelse i chat/plan.
# Napoli telles kun sesong >= 2015 ("siste ~5 år" per planen).
TOP_CLUBS = {
    281: ("Manchester City", "GB1", None),
    31: ("Liverpool FC", "GB1", None),
    11: ("Arsenal FC", "GB1", None),
    631: ("Chelsea FC", "GB1", None),
    985: ("Manchester United", "GB1", None),
    148: ("Tottenham Hotspur", "GB1", None),
    418: ("Real Madrid", "ES1", None),
    131: ("FC Barcelona", "ES1", None),
    13: ("Atlético de Madrid", "ES1", None),
    506: ("Juventus FC", "IT1", None),
    46: ("Inter Milan", "IT1", None),
    5: ("AC Milan", "IT1", None),
    6195: ("SSC Napoli", "IT1", 2015),
    12: ("AS Roma", "IT1", None),
    27: ("Bayern Munich", "L1", None),
    16: ("Borussia Dortmund", "L1", None),
    583: ("Paris Saint-Germain", "FR1", None),
}
TOP_CLUB_IDS = set(TOP_CLUBS.keys())


def date_to_season(date: pd.Series) -> pd.Series:
    """Transfermarkt seasons run ~Aug(year) - Jun(year+1); label = year."""
    return date.dt.year - (date.dt.month < 7).astype(int)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Laster data...")
    appearances = pd.read_csv(RAW_DIR / "appearances.csv", low_memory=False)
    games = pd.read_csv(RAW_DIR / "games.csv", low_memory=False)[["game_id", "season"]]
    players = pd.read_csv(RAW_DIR / "players.csv", low_memory=False)
    clubs = pd.read_csv(RAW_DIR / "clubs.csv", low_memory=False)[["club_id", "name"]]
    valuations = pd.read_csv(RAW_DIR / "player_valuations.csv")

    app = appearances[appearances["competition_id"].isin(TOP5_LEAGUES)].merge(
        games, on="game_id", how="left"
    )
    print(f"Appearances i topp 5-ligaer (all-time i kilden): {len(app):,}".replace(",", " "))

    in_period = app[
        (app["season"] >= PERIOD_START_SEASON) & (app["season"] <= PERIOD_END_SEASON)
    ]
    print(f"Appearances i topp 5-ligaer, 2012/13-2019/20: {len(in_period):,}".replace(",", " "))

    players_in_period = set(in_period["player_id"].unique())
    print(f"Unike spillere som spilte i topp 5 i perioden: {len(players_in_period):,}".replace(",", " "))

    # --- player_career_summary.csv (career = all-time i kilden, dvs. fra 2012-07-03) ---
    career_agg = (
        app.groupby("player_id")
        .agg(total_minutes_top5=("minutes_played", "sum"), total_appearances=("game_id", "count"))
        .reset_index()
    )

    ever_top_club_rows = []
    for club_id, (club_name, league, min_season) in TOP_CLUBS.items():
        sub = app[app["player_club_id"] == club_id]
        if min_season is not None:
            sub = sub[sub["season"] >= min_season]
        ever_top_club_rows.append(sub[["player_id"]].drop_duplicates())
    ever_top_club_ids = (
        pd.concat(ever_top_club_rows)["player_id"].unique() if ever_top_club_rows else []
    )
    ever_top_club_set = set(ever_top_club_ids)

    peak_value = valuations.groupby("player_id")["market_value_in_eur"].max().rename(
        "peak_market_value_eur"
    )

    # Hovedliga = ligaen der spilleren har flest minutter i studieperioden.
    primary_league = (
        in_period.groupby(["player_id", "competition_id"])["minutes_played"]
        .sum()
        .reset_index()
        .sort_values("minutes_played", ascending=False)
        .drop_duplicates("player_id")
        .set_index("player_id")["competition_id"]
        .rename("primary_league")
    )

    summary = career_agg.set_index("player_id")
    summary = summary.join(peak_value, how="left")
    summary = summary.join(primary_league, how="left")
    summary["ever_played_top_club"] = summary.index.isin(ever_top_club_set)
    summary["played_in_period"] = summary.index.isin(players_in_period)

    # Percentil-rang av peak-verdi blant spillere med samme hovedliga (kun
    # relevant/meningsfullt for studiepopulasjonen, dvs. played_in_period).
    in_pop = summary[summary["played_in_period"]]
    value_pct_in_league = in_pop.groupby("primary_league")["peak_market_value_eur"].rank(
        pct=True
    )
    summary["peak_value_pct_in_league"] = value_pct_in_league

    summary["passes_obscurity_filter"] = (
        (summary["total_minutes_top5"] <= MAX_MINUTES)
        & summary["played_in_period"]
        & (~summary["ever_played_top_club"])
        & (summary["peak_value_pct_in_league"] <= MARKET_VALUE_PERCENTILE_CUTOFF)
    )
    # Restrict output to the study population: players who actually appeared
    # in a top-5 league during 2012/13-2019/20 (pkt. 1 in the plan).
    summary = summary[summary["played_in_period"]].reset_index()
    summary.to_csv(OUT_DIR / "player_career_summary.csv", index=False)
    print(f"player_career_summary.csv: {len(summary):,} spillere".replace(",", " "))

    n_pass = int(summary["passes_obscurity_filter"].sum())
    print(f"  -> passerer obskuritetsfilter: {n_pass:,} ({n_pass / len(summary):.1%})".replace(",", " "))

    # --- player_seasons.csv (per periode 2012/13-2019/20) ---
    season_value = valuations.copy()
    season_value["date"] = pd.to_datetime(season_value["date"])
    season_value["season"] = date_to_season(season_value["date"])
    season_peak = (
        season_value.groupby(["player_id", "season"])["market_value_in_eur"]
        .max()
        .rename("market_value_eur")
    )

    seasons = (
        in_period.groupby(["player_id", "season", "competition_id", "player_club_id"])
        .agg(minutes_played=("minutes_played", "sum"), appearances=("game_id", "count"))
        .reset_index()
    )
    seasons = seasons.merge(clubs, left_on="player_club_id", right_on="club_id", how="left")
    seasons = seasons.merge(season_peak, on=["player_id", "season"], how="left")
    seasons = seasons.rename(columns={"competition_id": "league", "name": "club"})
    seasons = seasons[
        ["player_id", "season", "league", "club", "minutes_played", "appearances", "market_value_eur"]
    ].sort_values(["player_id", "season"])
    seasons.to_csv(OUT_DIR / "player_seasons.csv", index=False)
    print(f"player_seasons.csv: {len(seasons):,} rader".replace(",", " "))

    # --- players.csv (basis-info for studiepopulasjonen) ---
    players["birth_year"] = pd.to_datetime(players["date_of_birth"], errors="coerce").dt.year
    players_out = players[players["player_id"].isin(players_in_period)][
        ["player_id", "name", "birth_year", "country_of_citizenship", "position"]
    ].rename(columns={"country_of_citizenship": "nationality", "position": "primary_position"})
    players_out.to_csv(OUT_DIR / "players.csv", index=False)
    print(f"players.csv: {len(players_out):,} spillere".replace(",", " "))


if __name__ == "__main__":
    main()
