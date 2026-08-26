# Dataset-plan: "Mest obskure spiller" (Topp 5-ligaer)

## 1. Scope
- **Ligaer:** Premier League, La Liga, Serie A, Bundesliga, Ligue 1
- **Tidsperiode:** 2012/13 → 2019/20 (8 sesonger). Justert fra opprinnelig 2010/11 fordi `appearances.csv` (Kaggle-datasettet) ikke har data før 2012-07-03 — sesongene 2010/11 og 2011/12 er tomme i kilden. Spilleren må ha spilt minst noe i denne perioden, men karrieren kan strekke seg utenfor (før eller etter) — inkludert spillere som fortsatt er aktive i dag.

## 2. Filtreringskriterier (spilleren må matche ALLE)
| Kriterium | Definisjon | Åpne spørsmål |
|---|---|---|
| Maks minutter | ≤ 9 000 min totalt i karrieren i topp 5-ligaer (≈100 kamper). Kun ligaminutter — cup/europacup telles ikke med. Strammet inn fra opprinnelig 18 000/≈200 kamper — se begrunnelse under. | — avklart |
| Aldri i topplag | Har aldri spilt for et lag på "topplag-listen" (se pkt. 3), i noen sesong, i noen av de 5 ligaene (all-time i kildedataet, ikke bare 2012/13-2019/20 — se pkt. 1 for hvorfor "all-time" i praksis betyr "fra 2012-07-03"). Gjelder kun klubblag, ikke landslag. | — avklart |
| Maks markedsverdi | Har aldri hatt markedsverdi > 7M (GBP eller EUR — ingen konvertering, terskelen gjelder i den valutaen kilden oppgir). Justert fra opprinnelig 10M → 3M → 7M. | — avklart |

**Begrunnelse for innstramming:** Med opprinnelige terskler (18 000 min / 10M) passerte 68,4 % av de 7 062 spillerne i studiepopulasjonen — for bredt til å fange "obskure" spillere spesifikt. Minutter-terskelen ble satt til 9 000 (≈100 kamper). Markedsverdi-terskelen ble først satt til 3M, men testutvalget viste at flere rene rotasjonsspillere (Britton, Surman, Yacob, Mariappa) hadde en peak-verdi på 4-7M som unge lovende spillere uten noen gang å bli stjerner — 3M var for strengt og filtrerte bort disse. Justert opp til 7M.

## 3. Topplag-liste per liga (statisk, gjelder for hele perioden 2010-2020)

**Premier League:** Manchester City, Liverpool, Arsenal, Chelsea, Manchester United, Tottenham
*(Leicester regnes IKKE som topplag, til tross for tittelen i 2016)*

**La Liga:** Real Madrid, Barcelona, Atlético Madrid

**Serie A:** Juventus, Inter, AC Milan, Napoli (siste ~5 år), AS Roma

**Bundesliga:** Bayern München, Borussia Dortmund

**Ligue 1:** Paris Saint-Germain

## 4. Foreslått datasett-skjema

**players.csv**
- `player_id`
- `name`
- `birth_year`
- `nationality`
- `primary_position`

**player_seasons.csv** (én rad per spiller per sesong per klubb)
- `player_id`
- `season` (f.eks. "2015/16")
- `league`
- `club`
- `minutes_played`
- `appearances`
- `market_value_eur` (verdi ved sesongslutt, eller peak i sesongen)

**player_career_summary.csv** (aggregert, brukes til filtrering)
- `player_id`
- `total_minutes_top5`
- `total_appearances`
- `peak_market_value_gbp`
- `ever_played_top_club` (bool)
- `passes_obscurity_filter` (bool)

## 5. Datakilder (valgt)

**Hovedkilde: `transfermarkt-datasets` (dcaribou)**
- GitHub: https://github.com/dcaribou/transfermarkt-datasets
- Kaggle-speiling (samme data, enkel nedlasting): https://www.kaggle.com/datasets/davidcariboo/player-scores
- Gratis, oppdateres ukentlig, dekker alle 5 topp-ligaene
- Relevante tabeller:
  - `appearances` → ligaminutter/kamper per spiller per sesong per klubb
  - `player_valuations` → markedsverdi over tid (peak-verdi kan utledes)
  - `players` → grunnleggende spillerinfo
  - `clubs` / `games` → for å koble spiller til klubb/liga per sesong (nødvendig for topplag-filteret)

**Supplement (kun ved behov for kryssjekk): `worldfootballR`**
- R-pakke som kobler FBref ↔ Transfermarkt, men mapping dekker kun fra 2017/18 → mindre nyttig for hele 2010-2020-perioden, så brukes evt. kun til verifisering av enkeltspillere.

## 6. Neste steg
1. ~~Last ned `transfermarkt-datasets` (GitHub eller Kaggle) og inspiser skjema/kolonnenavn i praksis~~ ferdig
2. ~~Bygg filtreringslogikk på et lite utvalg spillere manuelt, verifiser mot kjente "obskure" spillere du kjenner til~~ ferdig (`scripts/filter_test.py`)
3. ~~Kjør full filtrering på hele datasettet for 2012/13-2019/20-perioden~~ ferdig (`scripts/build_dataset.py`) — 3 958 av 7 062 spillere passerer filteret
4. ~~Definer obscurity-metric~~ ferdig (`scripts/compute_obscurity_score.py`): `obscurity_score` = gjennomsnitt av inverterte percentil-ranger for `total_minutes_top5` og `peak_market_value_eur`, blant spillere som passerer filteret OG har >= 30 kamper i topp 5-ligaer (utelukker rene cameo-spillere). Output: `data/processed/obscurity_ranking_top50.csv` / `obscurity_ranking_full.csv`.
5. Bygg side kompiser kan gå inn på (neste steg, ikke påbegynt)
