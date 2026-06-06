import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

st.set_page_config(page_title="FIFA Tracker", page_icon="⚽", layout="wide")

MATCH_FILE = Path("matches.csv")

DEFAULT_MATCHES = pd.DataFrame([
    {"Match ID": 1, "Group": "A", "Date": "2026-06-11", "Team A": "Mexico", "Team B": "South Africa", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Azteca"},
    {"Match ID": 2, "Group": "A", "Date": "2026-06-11", "Team A": "South Korea", "Team B": "Czechia", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Akron"},
    {"Match ID": 3, "Group": "D", "Date": "2026-06-12", "Team A": "United States", "Team B": "Paraguay", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "SoFi Stadium"},
    {"Match ID": 4, "Group": "C", "Date": "2026-06-13", "Team A": "Brazil", "Team B": "Morocco", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 5, "Group": "I", "Date": "2026-06-16", "Team A": "France", "Team B": "Senegal", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
])

def load_matches():
    if MATCH_FILE.exists():
        return pd.read_csv(MATCH_FILE)
    return DEFAULT_MATCHES.copy()

def save_matches(df):
    df.to_csv(MATCH_FILE, index=False)

def ensure_columns(df):
    cols = ["Match ID", "Group", "Date", "Team A", "Team B", "Team A Score", "Team B Score", "Winner", "Loser", "Status", "Venue"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    return df[cols].fillna("")

def compute_match_outcome(row):
    try:
        sa = row["Team A Score"]
        sb = row["Team B Score"]
        if sa == "" or sb == "":
            return row
        sa = int(sa)
        sb = int(sb)
        if sa > sb:
            row["Winner"] = row["Team A"]
            row["Loser"] = row["Team B"]
            row["Status"] = "Finished"
        elif sb > sa:
            row["Winner"] = row["Team B"]
            row["Loser"] = row["Team A"]
            row["Status"] = "Finished"
        else:
            row["Winner"] = "Draw"
            row["Loser"] = "Draw"
            row["Status"] = "Finished"
    except Exception:
        pass
    return row

def next_opponent(team, matches):
    future = matches[(matches["Status"] != "Finished") & ((matches["Team A"] == team) | (matches["Team B"] == team))]
    if len(future) == 0:
        return ""
    r = future.sort_values(["Date", "Match ID"]).iloc[0]
    return r["Team B"] if r["Team A"] == team else r["Team A"]

def build_standings(matches):
    rows = []
    teams = pd.unique(matches[["Team A", "Team B"]].values.ravel("K"))
    teams = [t for t in teams if t and str(t).strip()]
    for team in teams:
        group = matches[(matches["Team A"] == team) | (matches["Team B"] == team)]["Group"].dropna()
        group = group.iloc[0] if len(group) else ""
        rows.append({"Group": group, "Team": team, "P": 0, "W": 0, "D": 0, "L": 0, "GF": 0, "GA": 0, "Pts": 0})
    stg = pd.DataFrame(rows).drop_duplicates(subset=["Group", "Team"]).set_index(["Group", "Team"])

    for _, r in matches.iterrows():
        if r["Status"] != "Finished":
            continue
        try:
            sa = int(r["Team A Score"])
            sb = int(r["Team B Score"])
        except Exception:
            continue
        g = r["Group"]
        a = r["Team A"]
        b = r["Team B"]
        for t, gf, ga in [(a, sa, sb), (b, sb, sa)]:
            stg.loc[(g, t), "P"] += 1
            stg.loc[(g, t), "GF"] += gf
            stg.loc[(g, t), "GA"] += ga
        if sa > sb:
            stg.loc[(g, a), "W"] += 1
            stg.loc[(g, a), "Pts"] += 3
            stg.loc[(g, b), "L"] += 1
        elif sb > sa:
            stg.loc[(g, b), "W"] += 1
            stg.loc[(g, b), "Pts"] += 3
            stg.loc[(g, a), "L"] += 1
        else:
            stg.loc[(g, a), "D"] += 1
            stg.loc[(g, b), "D"] += 1
            stg.loc[(g, a), "Pts"] += 1
            stg.loc[(g, b), "Pts"] += 1

    out = stg.reset_index()
    out["GD"] = out["GF"] - out["GA"]
    out = out.sort_values(["Group", "Pts", "GD", "GF", "Team"], ascending=[True, False, False, False, True])
    return out

def rank_third_places(standings):
    thirds = standings.groupby("Group").head(3)
    thirds = thirds.sort_values(["Pts", "GD", "GF", "Team"], ascending=[False, False, False, True])
    return thirds.head(8)

def get_qualifiers(standings):
    top_two = standings.groupby("Group").head(2)
    best_thirds = rank_third_places(standings)
    qualifiers = pd.concat([top_two, best_thirds], ignore_index=True)
    return qualifiers.sort_values(["Group", "Pts", "GD", "GF"], ascending=[True, False, False, False])

def build_round_of_32(qualifiers):
    q = qualifiers.reset_index(drop=True)
    pairs = []
    for i in range(0, len(q), 2):
        if i + 1 < len(q):
            pairs.append({
                "Match": f"R32-{i//2 + 1}",
                "Team A": q.loc[i, "Team"],
                "Team B": q.loc[i + 1, "Team"],
                "Status": "Upcoming",
                "Winner": "",
                "Loser": ""
            })
    return pd.DataFrame(pairs)

if "matches" not in st.session_state:
    st.session_state.matches = ensure_columns(load_matches())

if st_autorefresh:
    st_autorefresh(interval=300000, key="refresh")

st.title("⚽ FIFA Tracker")
st.caption(f"Last refresh: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

st.session_state.matches = ensure_columns(st.session_state.matches)
st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)

# FIX: standings must be computed before tabs so tab3 (Bracket) can access it
standings = build_standings(st.session_state.matches)

tab1, tab2, tab3 = st.tabs(["Fixtures", "Standings", "Bracket"])

with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("Matches", len(st.session_state.matches))
    c2.metric("Finished", int((st.session_state.matches["Status"] == "Finished").sum()))
    c3.metric("Upcoming", int((st.session_state.matches["Status"] == "Upcoming").sum()))

    edited = st.data_editor(
        st.session_state.matches,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Match ID": st.column_config.NumberColumn("Match ID", disabled=True),
            "Group": st.column_config.TextColumn("Group"),
            "Date": st.column_config.TextColumn("Date"),
            "Team A": st.column_config.TextColumn("Team A"),
            "Team B": st.column_config.TextColumn("Team B"),
            "Team A Score": st.column_config.TextColumn("Team A Score"),
            "Team B Score": st.column_config.TextColumn("Team B Score"),
            "Winner": st.column_config.TextColumn("Winner", disabled=True),
            "Loser": st.column_config.TextColumn("Loser", disabled=True),
            "Status": st.column_config.SelectboxColumn("Status", options=["Upcoming", "Finished"]),
            "Venue": st.column_config.TextColumn("Venue"),
        },
        key="fixtures_editor",
    )

    save_col, download_col = st.columns(2)
    with save_col:
        if st.button("Save fixtures", use_container_width=True):
            st.session_state.matches = ensure_columns(edited.copy())
            st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)
            save_matches(st.session_state.matches)
            st.success("Saved.")
    with download_col:
        st.download_button(
            "Download CSV",
            data=edited.to_csv(index=False).encode("utf-8"),
            file_name="matches.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("### Next opponent for each team")
    teams = pd.unique(st.session_state.matches[["Team A", "Team B"]].values.ravel("K"))
    teams = [t for t in teams if t and str(t).strip()]
    next_data = []
    for t in teams:
        next_data.append({
            "Team": t,
            "Next Opponent": next_opponent(t, st.session_state.matches)
        })
    if next_data:
        st.dataframe(pd.DataFrame(next_data), use_container_width=True, hide_index=True)

with tab2:
    if len(standings):
        st.dataframe(standings, use_container_width=True, hide_index=True)
    else:
        st.info("Add finished matches to generate standings.")

with tab3:
    st.markdown("### Round of 32")
    qualifiers = get_qualifiers(standings)
    if len(qualifiers):
        st.dataframe(qualifiers.reset_index(drop=True), use_container_width=True, hide_index=True)
        r32 = build_round_of_32(qualifiers)
        st.markdown("### Round of 32 matches")
        st.dataframe(r32, use_container_width=True, hide_index=True)
    else:
        st.info("Finish group matches to generate Round of 32.")
