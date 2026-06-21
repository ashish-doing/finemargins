"""
pipeline/features.py
Builds the PressureFeatures rows (see contracts.py) from the raw shot
datasets pulled by fetch_statsbomb.py. Pure pandas, no IBM dependency —
keeps this module testable without any cloud credentials.
"""

import pandas as pd
import numpy as np

STAGE_WEIGHT = {
    "Group Stage": 0.0,
    "Round of 16": 0.4,
    "Quarter-finals": 0.6,
    "Semi-finals": 0.8,
    "3rd Place Final": 0.7,
    "Final": 1.0,
}

PERIOD_END_MINUTE = {1: 45, 2: 90, 3: 105, 4: 120}


def minutes_remaining(period: int, minute: int) -> float:
    if period == 5:
        return 0.0  # shootout has no "time remaining" concept
    end = PERIOD_END_MINUTE.get(period, 90)
    return max(end - minute, 0)


def build_penalty_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds pressure columns to the 202-row penalty dataset."""
    df = df.copy()
    df["is_goal"] = (df["outcome"] == "Goal").astype(int)
    df["stage_weight"] = df["stage"].map(STAGE_WEIGHT).fillna(0.0)
    df["is_knockout"] = (df["stage"] != "Group Stage").astype(int)

    # kick order within a shootout: rank by minute within (match_id, period==5)
    df["kick_order"] = 0
    mask = df["is_shootout"]
    df.loc[mask, "kick_order"] = (
        df[mask].groupby("match_id")["minute"].rank(method="first").astype(int)
    )
    # sudden death = beyond the first 10 kicks (5 per team) of a shootout
    df["is_sudden_death"] = ((df["kick_order"] > 10) & df["is_shootout"]).astype(int)
    return df


def build_late_shot_features(df: pd.DataFrame) -> pd.DataFrame:
    """Adds pressure columns to the 1228-row late/extra-time shot dataset."""
    df = df.copy()
    df["is_goal"] = (df["outcome"] == "Goal").astype(int)
    df["stage_weight"] = df["stage"].map(STAGE_WEIGHT).fillna(0.0)
    df["is_knockout"] = (df["stage"] != "Group Stage").astype(int)
    df["minutes_remaining"] = df.apply(
        lambda r: minutes_remaining(r["period"], r["minute"]), axis=1
    )
    df["is_extra_time"] = (df["period"].isin([3, 4])).astype(int)
    # residual = how much better/worse than the baseline xG model expected
    df["xg_residual"] = df["is_goal"] - df["xg"]
    return df


if __name__ == "__main__":
    import json, urllib.request
    from concurrent.futures import ThreadPoolExecutor
    import os

    os.makedirs("data/processed", exist_ok=True)

    print("Fetching match index from StatsBomb...")
    tournaments = [(43, 106, "2022 WC"), (43, 3, "2018 WC"), (72, 107, "WWC 2023")]
    all_match_ids, match_meta = [], {}
    for comp, season, label in tournaments:
        url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{comp}/{season}.json"
        data = json.loads(urllib.request.urlopen(url).read())
        for m in data:
            all_match_ids.append(m["match_id"])
            match_meta[m["match_id"]] = {
                "tournament": label,
                "stage": m["competition_stage"]["name"],
                "home": m["home_team"]["home_team_name"],
                "away": m["away_team"]["away_team_name"],
            }
        print(f"  {label}: {len(data)} matches")

    print(f"Fetching events for {len(all_match_ids)} matches (~30s)...")
    def fetch(mid):
        url = f"https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{mid}.json"
        try: return mid, json.loads(urllib.request.urlopen(url, timeout=20).read())
        except: return mid, None

    events_all = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        for mid, data in ex.map(fetch, all_match_ids):
            events_all[mid] = data
    print(f"  Fetched {sum(1 for v in events_all.values() if v)} matches")

    print("Extracting shots...")
    penalty_shots, late_shots = [], []
    for mid, events in events_all.items():
        if not events: continue
        meta = match_meta[mid]
        for e in events:
            if e.get("type", {}).get("name") != "Shot": continue
            shot = e["shot"]
            is_pen = shot.get("type", {}).get("name") == "Penalty"
            period, minute = e.get("period"), e.get("minute")
            rec = {
                "match_id": mid, "tournament": meta["tournament"],
                "stage": meta["stage"], "player": e["player"]["name"],
                "team": e.get("team", {}).get("name", "Unknown"),
                "period": period, "minute": minute,
                "outcome": shot["outcome"]["name"],
                "xg": shot.get("statsbomb_xg"),
                "is_shootout": period == 5,
            }
            if is_pen:
                penalty_shots.append(rec)
            elif (period in (1, 2) and minute >= 75) or period in (3, 4):
                late_shots.append(rec)

    pd.DataFrame(penalty_shots).to_parquet("data/processed/penalty_dataset.parquet", index=False)
    pd.DataFrame(late_shots).to_parquet("data/processed/late_shots_dataset.parquet", index=False)
    print(f"Saved: {len(penalty_shots)} penalties, {len(late_shots)} late shots")

    pen = pd.read_parquet("data/processed/penalty_dataset.parquet")
    late = pd.read_parquet("data/processed/late_shots_dataset.parquet")
    pen_feat = build_penalty_features(pen)
    late_feat = build_late_shot_features(late)
    pen_feat.to_parquet("data/processed/penalty_features.parquet", index=False)
    late_feat.to_parquet("data/processed/late_shot_features.parquet", index=False)
    print("Penalty features:", pen_feat.shape)
    print("Late-shot features:", late_feat.shape)
    print("Done.")