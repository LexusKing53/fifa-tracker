import pandas as pd


TEAM_ALIASES = {
    "Cabo Verde": "Cape Verde",
    "Cape Verde": "Cape Verde",
}

KNOWN_FINAL_RESULTS = {
    ("2026-06-15", "Spain", "Cape Verde"): (0, 0),
}


def normalize_result_team_name(name):
    team = str(name).strip()
    return TEAM_ALIASES.get(team, team)


def _normalize(name, normalizer=None):
    if normalizer:
        return normalizer(name)
    return normalize_result_team_name(name)


def _known_result_for(row, normalizer=None):
    date = str(row.get("Date", "")).strip()
    team_a = _normalize(row.get("Team A", ""), normalizer)
    team_b = _normalize(row.get("Team B", ""), normalizer)

    direct_key = (date, team_a, team_b)
    if direct_key in KNOWN_FINAL_RESULTS:
        return KNOWN_FINAL_RESULTS[direct_key]

    reverse_key = (date, team_b, team_a)
    if reverse_key in KNOWN_FINAL_RESULTS:
        score_b, score_a = KNOWN_FINAL_RESULTS[reverse_key]
        return score_a, score_b

    return None


def compute_match_outcome(row):
    try:
        sa, sb = row["Team A Score"], row["Team B Score"]
        if sa == "" or sb == "":
            return row
        sa, sb = int(sa), int(sb)
        if sa > sb:
            row["Winner"], row["Loser"], row["Status"] = row["Team A"], row["Team B"], "Finished"
        elif sb > sa:
            row["Winner"], row["Loser"], row["Status"] = row["Team B"], row["Team A"], "Finished"
        else:
            row["Winner"], row["Loser"], row["Status"] = "Draw", "Draw", "Finished"
    except Exception:
        pass
    return row


def apply_known_final_results(matches_df, normalizer=None):
    updated = matches_df.copy()
    for idx, row in updated.iterrows():
        result = _known_result_for(row, normalizer)
        if result is None:
            continue

        score_a, score_b = result
        updated.at[idx, "Team A Score"] = str(score_a)
        updated.at[idx, "Team B Score"] = str(score_b)
        updated.loc[idx] = compute_match_outcome(updated.loc[idx].copy())

    return updated


def build_standings(matches):
    rows = []
    teams = pd.unique(matches[["Team A", "Team B"]].values.ravel("K"))
    teams = [t for t in teams if t and str(t).strip()]
    for team in teams:
        group = matches[(matches["Team A"] == team) | (matches["Team B"] == team)]["Group"].dropna()
        group = group.iloc[0] if len(group) else ""
        rows.append({"Group": group, "Team": team, "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "Pts": 0})
    if not rows:
        return pd.DataFrame(columns=["Group", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"])
    stg = pd.DataFrame(rows).drop_duplicates(subset=["Group", "Team"]).set_index(["Group", "Team"])
    for _, r in matches.iterrows():
        if r["Status"] != "Finished":
            continue
        try:
            sa, sb = int(r["Team A Score"]), int(r["Team B Score"])
        except Exception:
            continue
        g, a, b = r["Group"], r["Team A"], r["Team B"]
        for t, gf, ga in [(a, sa, sb), (b, sb, sa)]:
            stg.loc[(g, t), "P"] += 1
            stg.loc[(g, t), "GF"] += gf
            stg.loc[(g, t), "GA"] += ga
        if sa > sb:
            stg.loc[(g, a), "W"] += 1; stg.loc[(g, a), "Pts"] += 3; stg.loc[(g, b), "L"] += 1
        elif sb > sa:
            stg.loc[(g, b), "W"] += 1; stg.loc[(g, b), "Pts"] += 3; stg.loc[(g, a), "L"] += 1
        else:
            stg.loc[(g, a), "D"] += 1; stg.loc[(g, b), "D"] += 1
            stg.loc[(g, a), "Pts"] += 1; stg.loc[(g, b), "Pts"] += 1
    out = stg.reset_index()
    out["GD"] = out["GF"] - out["GA"]
    return out.sort_values(["Group", "Pts", "GD", "GF", "Team"], ascending=[True, False, False, False, True])
