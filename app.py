import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import requests

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

st.set_page_config(page_title="FIFA 2026 Tracker", page_icon="⚽", layout="wide")

# ── API ──────────────────────────────────────────────────────────────────────
API_KEY = "f477119f97c044af967a2834846259a6"
API_BASE = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": API_KEY}
WC2026_ID = 2000  # FIFA World Cup competition ID

# ── FLAGS ────────────────────────────────────────────────────────────────────
FLAGS = {
    "Germany": "🇩🇪", "Brazil": "🇧🇷", "France": "🇫🇷", "Argentina": "🇦🇷",
    "Spain": "🇪🇸", "England": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "Portugal": "🇵🇹", "Netherlands": "🇳🇱",
    "Belgium": "🇧🇪", "Italy": "🇮🇹", "Croatia": "🇭🇷", "Uruguay": "🇺🇾",
    "Mexico": "🇲🇽", "United States": "🇺🇸", "USA": "🇺🇸", "Canada": "🇨🇦",
    "Morocco": "🇲🇦", "Senegal": "🇸🇳", "Japan": "🇯🇵", "South Korea": "🇰🇷",
    "Australia": "🇦🇺", "Switzerland": "🇨🇭", "Denmark": "🇩🇰", "Poland": "🇵🇱",
    "Serbia": "🇷🇸", "Ecuador": "🇪🇨", "Ghana": "🇬🇭", "Cameroon": "🇨🇲",
    "Tunisia": "🇹🇳", "Saudi Arabia": "🇸🇦", "Iran": "🇮🇷", "Qatar": "🇶🇦",
    "South Africa": "🇿🇦", "Nigeria": "🇳🇬", "Czechia": "🇨🇿", "Paraguay": "🇵🇾",
    "Colombia": "🇨🇴", "Venezuela": "🇻🇪", "Chile": "🇨🇱", "Peru": "🇵🇪",
    "Turkey": "🇹🇷", "Ukraine": "🇺🇦", "Austria": "🇦🇹", "Hungary": "🇭🇺",
    "Romania": "🇷🇴", "Slovakia": "🇸🇰", "Slovenia": "🇸🇮", "Albania": "🇦🇱",
    "New Zealand": "🇳🇿", "Costa Rica": "🇨🇷", "Panama": "🇵🇦", "Honduras": "🇭🇳",
    "Guatemala": "🇬🇹", "Jamaica": "🇯🇲", "Trinidad and Tobago": "🇹🇹",
    "Egypt": "🇪🇬", "Algeria": "🇩🇿", "Ivory Coast": "🇨🇮", "Mali": "🇲🇱",
    "Angola": "🇦🇴", "DR Congo": "🇨🇩", "Kenya": "🇰🇪", "Zimbabwe": "🇿🇼",
    "Indonesia": "🇮🇩", "Thailand": "🇹🇭", "Vietnam": "🇻🇳", "Philippines": "🇵🇭",
    "Iraq": "🇮🇶", "Jordan": "🇯🇴", "UAE": "🇦🇪", "Uzbekistan": "🇺🇿",
    "Scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "Wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿", "Ireland": "🇮🇪", "Greece": "🇬🇷",
    "Bolivia": "🇧🇴", "Cuba": "🇨🇺", "El Salvador": "🇸🇻", "Nicaragua": "🇳🇮",
}

def flag(team):
    return FLAGS.get(team, "🏳️")

# ── GROUP COLORS ─────────────────────────────────────────────────────────────
GROUP_COLORS = {
    "A": "#FF6B6B", "B": "#FF9F43", "C": "#F7C948",
    "D": "#48D8A0", "E": "#48C9F7", "F": "#748CF7",
    "G": "#C874F7", "H": "#F774C8", "I": "#74F7E8", "J": "#F79F74",
    "K": "#A8F774", "L": "#F77474",
}

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif !important;
    background-color: #0a0e1a !important;
    color: #e8eaf0 !important;
}

h1, h2, h3 { font-family: 'Bebas Neue', sans-serif !important; letter-spacing: 2px; }

.stApp { background: linear-gradient(135deg, #0a0e1a 0%, #0d1528 50%, #0a1420 100%) !important; }

.metric-card {
    background: linear-gradient(135deg, #1a2035, #1e2845);
    border: 1px solid #2a3550;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}

.match-card {
    background: linear-gradient(135deg, #141928, #1a2235);
    border: 1px solid #252d45;
    border-radius: 14px;
    padding: 1rem 1.5rem;
    margin: 0.5rem 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 15px rgba(0,0,0,0.3);
    transition: transform 0.2s;
}

.match-card:hover { transform: translateY(-2px); border-color: #3a4a6a; }

.team-name { font-size: 1.1rem; font-weight: 600; }
.score-box {
    background: #0a0e1a;
    border: 2px solid #2a3a5a;
    border-radius: 8px;
    padding: 0.3rem 0.8rem;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.6rem;
    color: #F7C948;
    min-width: 60px;
    text-align: center;
}
.vs-text { color: #5a6a8a; font-size: 0.85rem; font-weight: 600; }

.group-badge {
    border-radius: 6px;
    padding: 2px 10px;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 0.9rem;
    font-weight: bold;
    letter-spacing: 1px;
}

.status-live {
    background: linear-gradient(90deg, #FF4444, #FF6B6B);
    color: white;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    animation: pulse 1.5s infinite;
}
.status-finished { background: #1e3a2a; color: #48D8A0; border-radius: 20px; padding: 2px 12px; font-size: 0.75rem; }
.status-upcoming { background: #1a2a3a; color: #748CF7; border-radius: 20px; padding: 2px 12px; font-size: 0.75rem; }

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

.player-card {
    background: linear-gradient(135deg, #141928, #1a2235);
    border: 1px solid #252d45;
    border-radius: 12px;
    padding: 1rem;
    text-align: center;
    transition: transform 0.2s;
}
.player-card:hover { transform: translateY(-3px); border-color: #F7C948; }

.stTabs [data-baseweb="tab-list"] { background: #0d1220 !important; border-radius: 10px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: #8a9ab5 !important; font-family: 'Bebas Neue', sans-serif !important; font-size: 1rem !important; letter-spacing: 1px; }
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, #F7C948, #FF9F43) !important; color: #0a0e1a !important; border-radius: 7px !important; }

.stDataFrame { border-radius: 10px; overflow: hidden; }
div[data-testid="stMetricValue"] { font-family: 'Bebas Neue', sans-serif !important; font-size: 2.2rem !important; color: #F7C948 !important; }
div[data-testid="stMetricLabel"] { color: #8a9ab5 !important; font-size: 0.8rem !important; text-transform: uppercase; letter-spacing: 1px; }

.bracket-match {
    background: linear-gradient(135deg, #141928, #1a2235);
    border: 1px solid #252d45;
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin: 4px 0;
    font-size: 0.9rem;
}
.bracket-winner { border-color: #F7C948; color: #F7C948; font-weight: 700; }
.section-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 2rem;
    letter-spacing: 3px;
    color: #F7C948;
    border-bottom: 2px solid #F7C948;
    padding-bottom: 0.3rem;
    margin: 1.5rem 0 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ── MATCH FILE ───────────────────────────────────────────────────────────────
MATCH_FILE = Path("matches.csv")

DEFAULT_MATCHES = pd.DataFrame([
    {"Match ID": 1,  "Group": "A", "Date": "2026-06-11", "Team A": "Mexico",       "Team B": "South Africa", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Azteca"},
    {"Match ID": 2,  "Group": "A", "Date": "2026-06-11", "Team A": "South Korea",  "Team B": "Czechia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Akron"},
    {"Match ID": 3,  "Group": "B", "Date": "2026-06-12", "Team A": "Argentina",    "Team B": "Chile",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 4,  "Group": "B", "Date": "2026-06-12", "Team A": "Peru",         "Team B": "Australia",    "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "SoFi Stadium"},
    {"Match ID": 5,  "Group": "C", "Date": "2026-06-13", "Team A": "Brazil",       "Team B": "Morocco",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 6,  "Group": "C", "Date": "2026-06-13", "Team A": "Croatia",      "Team B": "Algeria",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Levi's Stadium"},
    {"Match ID": 7,  "Group": "D", "Date": "2026-06-12", "Team A": "United States","Team B": "Paraguay",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "SoFi Stadium"},
    {"Match ID": 8,  "Group": "D", "Date": "2026-06-13", "Team A": "Ecuador",      "Team B": "Bolivia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "AT&T Stadium"},
    {"Match ID": 9,  "Group": "E", "Date": "2026-06-14", "Team A": "Spain",        "Team B": "Venezuela",    "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 10, "Group": "E", "Date": "2026-06-14", "Team A": "Turkey",       "Team B": "Serbia",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Gillette Stadium"},
    {"Match ID": 11, "Group": "F", "Date": "2026-06-14", "Team A": "Portugal",     "Team B": "Angola",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Allegiant Stadium"},
    {"Match ID": 12, "Group": "F", "Date": "2026-06-15", "Team A": "Germany",      "Team B": "Saudi Arabia", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "SoFi Stadium"},
    {"Match ID": 13, "Group": "G", "Date": "2026-06-15", "Team A": "England",      "Team B": "Nigeria",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 14, "Group": "G", "Date": "2026-06-15", "Team A": "Netherlands",  "Team B": "DR Congo",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Levi's Stadium"},
    {"Match ID": 15, "Group": "H", "Date": "2026-06-16", "Team A": "Colombia",     "Team B": "Ivory Coast",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "AT&T Stadium"},
    {"Match ID": 16, "Group": "H", "Date": "2026-06-16", "Team A": "Denmark",      "Team B": "Slovakia",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Gillette Stadium"},
    {"Match ID": 17, "Group": "I", "Date": "2026-06-16", "Team A": "France",       "Team B": "Senegal",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 18, "Group": "I", "Date": "2026-06-17", "Team A": "Uruguay",      "Team B": "Ghana",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "SoFi Stadium"},
    {"Match ID": 19, "Group": "J", "Date": "2026-06-17", "Team A": "Belgium",      "Team B": "Egypt",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Allegiant Stadium"},
    {"Match ID": 20, "Group": "J", "Date": "2026-06-17", "Team A": "Austria",      "Team B": "Ukraine",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Levi's Stadium"},
    {"Match ID": 21, "Group": "K", "Date": "2026-06-18", "Team A": "Japan",        "Team B": "Iraq",         "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "AT&T Stadium"},
    {"Match ID": 22, "Group": "K", "Date": "2026-06-18", "Team A": "Indonesia",    "Team B": "Cameroon",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Gillette Stadium"},
    {"Match ID": 23, "Group": "L", "Date": "2026-06-18", "Team A": "Switzerland",  "Team B": "Slovenia",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "MetLife Stadium"},
    {"Match ID": 24, "Group": "L", "Date": "2026-06-19", "Team A": "New Zealand",  "Team B": "Honduras",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "SoFi Stadium"},
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

def get_qualifiers(standings):
    if len(standings) == 0:
        return pd.DataFrame()
    top_two = standings.groupby("Group").head(2)
    thirds = standings.groupby("Group").nth(2).sort_values(["Pts", "GD", "GF"], ascending=[False, False, False]).head(8)
    return pd.concat([top_two, thirds], ignore_index=True)

def build_round_of_32(qualifiers):
    q = qualifiers.reset_index(drop=True)
    pairs = []
    for i in range(0, min(len(q), 32), 2):
        if i + 1 < len(q):
            pairs.append({"Match": f"R32-{i//2+1}", "Team A": q.loc[i, "Team"], "Team B": q.loc[i+1, "Team"], "Status": "Upcoming", "Winner": ""})
    return pd.DataFrame(pairs)

@st.cache_data(ttl=300)
def fetch_live_matches():
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/matches?status=LIVE", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("matches", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=300)
def fetch_todays_matches():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        r = requests.get(f"{API_BASE}/competitions/WC/matches?dateFrom={today}&dateTo={today}", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("matches", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=600)
def fetch_top_scorers():
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/scorers?limit=10", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("scorers", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=600)
def fetch_standings_api():
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/standings", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("standings", [])
    except Exception:
        pass
    return []

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "matches" not in st.session_state:
    st.session_state.matches = ensure_columns(load_matches())

if st_autorefresh:
    st_autorefresh(interval=60000, key="refresh")

st.session_state.matches = ensure_columns(st.session_state.matches)
st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)
standings = build_standings(st.session_state.matches)

# ── HEADER ────────────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.markdown("<div style='font-size:4rem;padding-top:0.2rem'>⚽</div>", unsafe_allow_html=True)
with col_title:
    st.markdown("<h1 style='font-size:3.5rem;margin:0;color:#F7C948'>FIFA WORLD CUP 2026</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#5a6a8a;margin:0;font-size:0.85rem'>🔄 Updated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)

st.markdown("---")

# ── LIVE SCORES BANNER ────────────────────────────────────────────────────────
live = fetch_live_matches()
if live:
    st.markdown("<div class='section-title'>🔴 LIVE NOW</div>", unsafe_allow_html=True)
    for m in live:
        ha = m["homeTeam"]["name"]; hb = m["awayTeam"]["name"]
        sa = m["score"]["fullTime"]["home"] or 0
        sb = m["score"]["fullTime"]["away"] or 0
        st.markdown(f"""
        <div class='match-card'>
            <span class='team-name'>{flag(ha)} {ha}</span>
            <div style='text-align:center'>
                <div class='score-box'>{sa} — {sb}</div>
                <span class='status-live'>● LIVE</span>
            </div>
            <span class='team-name'>{hb} {flag(hb)}</span>
        </div>""", unsafe_allow_html=True)

# ── METRICS ───────────────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
total = len(st.session_state.matches)
finished = int((st.session_state.matches["Status"] == "Finished").sum())
upcoming = int((st.session_state.matches["Status"] == "Upcoming").sum())
groups = st.session_state.matches["Group"].nunique()
m1.metric("⚽ Total Matches", total)
m2.metric("✅ Finished", finished)
m3.metric("🕐 Upcoming", upcoming)
m4.metric("🏟️ Groups", groups)

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 FIXTURES", "📊 STANDINGS", "🏆 BRACKET", "⭐ TOP PLAYERS", "📡 LIVE API"])

# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-title'>MATCH FIXTURES</div>", unsafe_allow_html=True)

    groups_list = sorted(st.session_state.matches["Group"].unique())
    sel_group = st.selectbox("Filter by Group", ["All Groups"] + [f"Group {g}" for g in groups_list])

    display_df = st.session_state.matches.copy()
    if sel_group != "All Groups":
        g_letter = sel_group.replace("Group ", "")
        display_df = display_df[display_df["Group"] == g_letter]

    for _, row in display_df.iterrows():
        grp_color = GROUP_COLORS.get(str(row["Group"]), "#748CF7")
        status_html = (
            "<span class='status-live'>● LIVE</span>" if row["Status"] == "Live"
            else "<span class='status-finished'>✓ FT</span>" if row["Status"] == "Finished"
            else "<span class='status-upcoming'>⏱ Soon</span>"
        )
        sa = row["Team A Score"] if row["Team A Score"] != "" else "—"
        sb = row["Team B Score"] if row["Team B Score"] != "" else "—"
        st.markdown(f"""
        <div class='match-card'>
            <div style='display:flex;align-items:center;gap:8px;min-width:180px'>
                <span class='group-badge' style='background:{grp_color}22;color:{grp_color};border:1px solid {grp_color}44'>GRP {row["Group"]}</span>
                <span style='color:#5a6a8a;font-size:0.8rem'>{row["Date"]}</span>
            </div>
            <div style='display:flex;align-items:center;gap:12px;flex:1;justify-content:center'>
                <span class='team-name'>{flag(row["Team A"])} {row["Team A"]}</span>
                <div style='text-align:center'>
                    <div class='score-box'>{sa} : {sb}</div>
                    {status_html}
                </div>
                <span class='team-name'>{row["Team B"]} {flag(row["Team B"])}</span>
            </div>
            <span style='color:#5a6a8a;font-size:0.8rem;min-width:120px;text-align:right'>🏟️ {row["Venue"]}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>EDIT SCORES</div>", unsafe_allow_html=True)
    edited = st.data_editor(
        st.session_state.matches,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Match ID": st.column_config.NumberColumn("ID", disabled=True),
            "Group": st.column_config.TextColumn("Grp"),
            "Date": st.column_config.TextColumn("Date"),
            "Team A": st.column_config.TextColumn("Team A"),
            "Team B": st.column_config.TextColumn("Team B"),
            "Team A Score": st.column_config.TextColumn("Score A"),
            "Team B Score": st.column_config.TextColumn("Score B"),
            "Winner": st.column_config.TextColumn("Winner", disabled=True),
            "Loser": st.column_config.TextColumn("Loser", disabled=True),
            "Status": st.column_config.SelectboxColumn("Status", options=["Upcoming", "Finished"]),
            "Venue": st.column_config.TextColumn("Venue"),
        },
        key="fixtures_editor",
    )

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save Fixtures", use_container_width=True):
            st.session_state.matches = ensure_columns(edited.copy())
            st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)
            save_matches(st.session_state.matches)
            st.success("✅ Saved!")
    with c2:
        st.download_button("⬇️ Download CSV", data=edited.to_csv(index=False).encode("utf-8"),
                           file_name="matches.csv", mime="text/csv", use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-title'>GROUP STANDINGS</div>", unsafe_allow_html=True)
    if len(standings) == 0:
        st.info("Enter match scores to generate standings.")
    else:
        for grp in sorted(standings["Group"].unique()):
            grp_color = GROUP_COLORS.get(str(grp), "#748CF7")
            grp_df = standings[standings["Group"] == grp].copy()
            grp_df["Flag"] = grp_df["Team"].apply(flag)
            grp_df["Team"] = grp_df.apply(lambda r: f"{r['Flag']} {r['Team']}", axis=1)
            grp_df = grp_df[["Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]].reset_index(drop=True)
            grp_df.index = grp_df.index + 1

            st.markdown(f"<h3 style='color:{grp_color};font-family:Bebas Neue,sans-serif;letter-spacing:2px'>GROUP {grp}</h3>", unsafe_allow_html=True)
            st.dataframe(grp_df, use_container_width=True)
            st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>TOURNAMENT BRACKET</div>", unsafe_allow_html=True)
    qualifiers = get_qualifiers(standings)

    if len(qualifiers) < 4:
        st.info("🏆 Complete group stage matches to populate the bracket.")
        st.markdown("**Bracket structure:** 12 groups × top 2 + 8 best 3rd place = **32 teams** advance to Round of 32")
    else:
        r32 = build_round_of_32(qualifiers)
        st.markdown("### Round of 32")
        cols = st.columns(4)
        for i, (_, row) in enumerate(r32.iterrows()):
            with cols[i % 4]:
                winner_class = "bracket-winner" if row["Winner"] else ""
                st.markdown(f"""
                <div class='bracket-match {winner_class}'>
                    <div>{flag(row["Team A"])} {row["Team A"]}</div>
                    <div style='color:#5a6a8a;font-size:0.75rem;text-align:center'>vs</div>
                    <div>{flag(row["Team B"])} {row["Team B"]}</div>
                    {"<div style='color:#F7C948;font-size:0.8rem;margin-top:4px'>🏆 " + row["Winner"] + "</div>" if row["Winner"] else ""}
                </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-title'>TOP PERFORMERS</div>", unsafe_allow_html=True)
    scorers = fetch_top_scorers()

    if scorers:
        st.markdown("### ⚽ Top Scorers")
        cols = st.columns(5)
        for i, s in enumerate(scorers[:10]):
            with cols[i % 5]:
                player = s.get("player", {})
                team = s.get("team", {})
                goals = s.get("goals", 0)
                assists = s.get("assists", 0)
                name = player.get("name", "Unknown")
                team_name = team.get("name", "")
                st.markdown(f"""
                <div class='player-card'>
                    <div style='font-size:2rem'>{flag(team_name)}</div>
                    <div style='font-weight:700;font-size:0.9rem;margin:4px 0'>{name}</div>
                    <div style='color:#5a6a8a;font-size:0.75rem'>{team_name}</div>
                    <div style='color:#F7C948;font-size:1.4rem;font-family:Bebas Neue,sans-serif;margin-top:8px'>{goals} <span style='font-size:0.7rem;color:#8a9ab5'>GOALS</span></div>
                    <div style='color:#48D8A0;font-size:0.85rem'>{assists} assists</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Top scorer data will appear once the tournament begins.")
        st.markdown("""
        **What you'll see here when the tournament starts:**
        - 🥇 Top goal scorers with live counts
        - 🎯 Most assists
        - 📈 Player ratings
        - 🏅 Tournament awards tracker
        """)

    # Top teams by performance
    st.markdown("### 🏆 Top Performing Teams")
    if len(standings) > 0:
        top_teams = standings.nlargest(10, "Pts")[["Group", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]].copy()
        top_teams["Flag"] = top_teams["Team"].apply(flag)
        top_teams["Team"] = top_teams.apply(lambda r: f"{r['Flag']} {r['Team']}", axis=1)
        top_teams = top_teams.drop("Flag", axis=1).reset_index(drop=True)
        top_teams.index = top_teams.index + 1
        st.dataframe(top_teams, use_container_width=True)
    else:
        st.info("Team performance stats will populate as matches are played.")

# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-title'>LIVE API DATA</div>", unsafe_allow_html=True)

    if st.button("🔄 Refresh Live Data"):
        st.cache_data.clear()
        st.rerun()

    today_matches = fetch_todays_matches()
    if today_matches:
        st.markdown("### 📅 Today's Matches")
        for m in today_matches:
            ha = m["homeTeam"]["name"]; hb = m["awayTeam"]["name"]
            sa = m["score"]["fullTime"]["home"]
            sb = m["score"]["fullTime"]["away"]
            score_str = f"{sa} — {sb}" if sa is not None else "vs"
            status = m.get("status", "SCHEDULED")
            status_badge = "🔴 LIVE" if status == "IN_PLAY" else ("✅ FT" if status == "FINISHED" else "⏱ Upcoming")
            st.markdown(f"""
            <div class='match-card'>
                <span class='team-name'>{flag(ha)} {ha}</span>
                <div style='text-align:center'>
                    <div class='score-box'>{score_str}</div>
                    <div style='color:#8a9ab5;font-size:0.8rem'>{status_badge}</div>
                </div>
                <span class='team-name'>{hb} {flag(hb)}</span>
            </div>""", unsafe_allow_html=True)
    else:
        st.info("No matches today — or the tournament hasn't started yet. Live data will appear here automatically.")

    api_standings = fetch_standings_api()
    if api_standings:
        st.markdown("### 📊 Live Standings from API")
        for s in api_standings:
            st.markdown(f"**{s.get('group', 'Group')}**")
            rows = []
            for entry in s.get("table", []):
                team = entry["team"]["name"]
                rows.append({
                    "Pos": entry["position"],
                    "Team": f"{flag(team)} {team}",
                    "P": entry["playedGames"],
                    "W": entry["won"], "D": entry["draw"], "L": entry["lost"],
                    "GF": entry["goalsFor"], "GA": entry["goalsAgainst"],
                    "GD": entry["goalDifference"], "Pts": entry["points"]
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
