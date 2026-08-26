"""Test the obscurity filtering logic (see obskur-spiller-dataset-plan.md) on a
small, hand-picked set of players so the logic can be verified manually before
running on the full dataset.

Prints one row per (player, criterion) so every intermediate number can be
checked by eye. Some criteria are computed two ways (whole career vs. only
within the 2012/13-2019/20 study period) because the plan text is ambiguous
about scope in a couple of places -- those rows are marked INFO rather than
PASS/FAIL and are meant as a prompt for manual review, not automated logic.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

TOP5_LEAGUES = {"GB1", "ES1", "IT1", "L1", "FR1"}  # Premier League, La Liga, Serie A, Bundesliga, Ligue 1
PERIOD_START_SEASON = 2012  # 2012/13 -- justert fra 2010/11 pga. datahull i appearances.csv (ingen data før 2012-07-03)
PERIOD_END_SEASON = 2019  # 2019/20

MAX_MINUTES = 9_000  # ~100 kamper -- strammet inn fra 18 000 (se chat), 68 % passerte da
MAX_MARKET_VALUE_EUR = 7_000_000  # justert opp fra 3M etter testutvalg-sjekk (se chat)

# Topplag-liste fra obskur-spiller-dataset-plan.md, pkt. 3.
# Napoli telles kun de siste ~5 sesongene av perioden (planen sier "siste ~5 år") --
# tolket her som sesong >= 2015 (2015/16-2019/20). Flagg til bruker: dette er en
# antakelse, ikke eksplisitt avklart i planen.
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
    6195: ("SSC Napoli", "IT1", 2015),  # kun siste ~5 år av perioden
    12: ("AS Roma", "IT1", None),
    27: ("Bayern Munich", "L1", None),
    16: ("Borussia Dortmund", "L1", None),
    583: ("Paris Saint-Germain", "FR1", None),
}

# Håndplukket utvalg (player_id slått opp manuelt i players.csv, se chat-historikk).
# Noen navn var flertydige i datasettet -- disambiguert på fødselsår/kjent klubb:
#   - "Sergio Aguero" -> player_id 26399 (Sergio Agüero, f. 1988, Man City-legenden;
#     IKKE 354081, en annen/ukjent spiller med samme stavemåte uten aksent)
#   - "Lars Bender" -> player_id 30059 (IKKE tvillingbroren Sven Bender, id 29993)
PLAYERS = [
    (5957, "Alberto Aquilani"),
    (38145, "Adrian Mariappa"),
    (339556, "Rico Henry"),
    (46104, "Stevan Jovetić"),
    (26399, "Sergio Agüero"),
    (40043, "Leon Britton"),
    (29975, "Andrew Surman"),
    (399434, "Marcus Tavernier"),
    (45330, "Claudio Yacob"),
    (30059, "Lars Bender"),
]


def load_appearances_with_season() -> pd.DataFrame:
    app = pd.read_csv(RAW_DIR / "appearances.csv", low_memory=False)
    app = app[app["competition_id"].isin(TOP5_LEAGUES)]

    games = pd.read_csv(RAW_DIR / "games.csv", low_memory=False)[["game_id", "season"]]
    app = app.merge(games, on="game_id", how="left")
    return app


def add_row(rows, player_id, name, criterion, value, detail, result):
    rows.append(
        {
            "player_id": player_id,
            "name": name,
            "criterion": criterion,
            "value": value,
            "detail": detail,
            "result": result,
        }
    )


def main() -> None:
    app = load_appearances_with_season()
    in_period = app[(app["season"] >= PERIOD_START_SEASON) & (app["season"] <= PERIOD_END_SEASON)]

    valuations = pd.read_csv(RAW_DIR / "player_valuations.csv")
    peak_value_by_player = valuations.groupby("player_id")["market_value_in_eur"].max()

    rows = []

    for player_id, name in PLAYERS:
        career_rows = app[app["player_id"] == player_id]
        period_rows = in_period[in_period["player_id"] == player_id]

        career_minutes = int(career_rows["minutes_played"].sum())
        period_minutes = int(period_rows["minutes_played"].sum())
        career_apps = int(len(career_rows))
        period_apps = int(len(period_rows))

        add_row(
            rows, player_id, name, "Ligaminutter, hele karrieren (topp 5)",
            career_minutes, f"terskel <= {MAX_MINUTES}",
            "PASS" if career_minutes <= MAX_MINUTES else "FAIL",
        )
        add_row(
            rows, player_id, name, "Ligaminutter, kun 2012/13-2019/20",
            period_minutes, "INFO -- planen bruker karriere-total, ikke periode-total",
            "INFO",
        )
        add_row(
            rows, player_id, name, "Ligakamper, hele karrieren (topp 5)",
            career_apps, "referanse: ~100 kamper",
            "INFO",
        )
        add_row(
            rows, player_id, name, "Ligakamper, kun 2012/13-2019/20",
            period_apps, "-",
            "INFO",
        )

        played_in_period = period_apps > 0
        add_row(
            rows, player_id, name, "Spilte i topp 5 i perioden 2012-2020",
            played_in_period, "krav for å være i utvalget (pkt. 1)",
            "PASS" if played_in_period else "FAIL",
        )

        def top_club_hits(df: pd.DataFrame) -> list[str]:
            hits = []
            for club_id, (club_name, league, min_season) in TOP_CLUBS.items():
                sub = df[df["player_club_id"] == club_id]
                if min_season is not None:
                    sub = sub[sub["season"] >= min_season]
                if len(sub) > 0:
                    seasons = sorted(sub["season"].dropna().unique().tolist())
                    hits.append(f"{club_name} ({seasons[0]}-{seasons[-1]})")
            return hits

        career_hits = top_club_hits(career_rows)
        period_hits = top_club_hits(period_rows)

        add_row(
            rows, player_id, name, "Noensinne spilt for topplag (all-time)",
            len(career_hits) > 0, "; ".join(career_hits) if career_hits else "-",
            "FAIL" if career_hits else "PASS",
        )
        add_row(
            rows, player_id, name, "Spilt for topplag i perioden 2012-2020",
            len(period_hits) > 0, "; ".join(period_hits) if period_hits else "-",
            "INFO",
        )

        peak_value = peak_value_by_player.get(player_id)
        if pd.isna(peak_value) or peak_value is None:
            add_row(rows, player_id, name, "Peak markedsverdi (EUR)", None, "ingen data funnet", "INFO")
            peak_value_ok = None
        else:
            peak_value = int(peak_value)
            peak_value_ok = peak_value <= MAX_MARKET_VALUE_EUR
            add_row(
                rows, player_id, name, "Peak markedsverdi (EUR)",
                peak_value, f"terskel <= {MAX_MARKET_VALUE_EUR:,}".replace(",", " "),
                "PASS" if peak_value_ok else "FAIL",
            )

        passes = (
            career_minutes <= MAX_MINUTES
            and played_in_period
            and not career_hits
            and bool(peak_value_ok)
        )
        add_row(
            rows, player_id, name, "TOTAL: passerer obskuritetsfilter",
            passes, "kombinerer karriere-minutter, all-time topplag, peak-verdi",
            "PASS" if passes else "FAIL",
        )

    result_df = pd.DataFrame(rows)
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_colwidth", 60)
    pd.set_option("display.width", 160)

    for player_id, name in PLAYERS:
        print(f"\n{'=' * 100}")
        print(f"{name} (player_id={player_id})")
        print(f"{'=' * 100}")
        subset = result_df[result_df["player_id"] == player_id].drop(columns=["player_id", "name"])
        print(subset.to_string(index=False))


if __name__ == "__main__":
    main()
