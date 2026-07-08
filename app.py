import pandas as pd
import streamlit as st
from pathlib import Path
from datetime import datetime
import html
import requests
import bracket_store
from fixture_utils import sort_matches_by_kickoff, today_et, todays_matches_for_display
from match_lock import is_match_locked
from match_results import apply_known_final_results, build_standings, compute_match_outcome
from prediction_logic import filter_predictions_to_catalog, prediction_result_for_pick, score_predictions
from prediction_matches import (
    ROUND_OF_32_PREDICTION_MATCHES,
    build_prediction_match_catalog,
    build_round_of_16_from_round_of_32,
)
from seed_restore import (
    repair_bracket_store_from_seed,
    restore_bracket_store_if_missing,
)
from prediction_store import load_predictions, save_prediction, save_predictions
from translations import LANGUAGES, t

clear_bracket = bracket_store.clear_bracket
load_bracket = bracket_store.load_bracket
restore_bracket_round = bracket_store.restore_bracket_round
save_bracket_round = bracket_store.save_bracket_round
apply_live_match_results = getattr(bracket_store, "apply_live_match_results", lambda round_df, live_matches: round_df)

st.set_page_config(page_title="FIFA 2026 Tracker", page_icon="⚽", layout="wide")

# ── API ──────────────────────────────────────────────────────────────────────
def get_secret(name):
    try:
        return st.secrets.get(name, "")
    except Exception:
        return ""

API_KEY = get_secret("FOOTBALL_API_KEY")
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
    "Turkey": "🇹🇷", "Sweden": "🇸🇪", "Ukraine": "🇺🇦", "Austria": "🇦🇹", "Hungary": "🇭🇺",
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

TEAM_ALIASES = {
    "Türkiye": "Turkey",
    "Turkey": "Turkey",
    "Côte d’Ivoire": "Ivory Coast",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Curaçao": "Curacao",
    "Curacao": "Curacao",
    "Cabo Verde": "Cape Verde",
    "Cape Verde": "Cape Verde",
    "Korea Republic": "South Korea",
    "Republic of Korea": "South Korea",
    "IR Iran": "Iran",
    "Islamic Republic of Iran": "Iran",
    "Congo DR": "DR Congo",
    "DR Congo": "DR Congo",
    "USA": "United States",
    "United States of America": "United States",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}


def normalize_team_name(name):
    team = str(name).strip()
    return TEAM_ALIASES.get(team, team)


# ── SPINNING BALL CSS ────────────────────────────────────────────────────────
SPIN_BALL = """<span style='display:inline-block;animation:spin 2s linear infinite;font-size:3.5rem'>⚽</span>
<style>@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }</style>"""

# ── KEY PLAYERS ──────────────────────────────────────────────────────────────
KEY_PLAYERS = {
    "Argentina":   [("Lionel Messi","Forward","Inter Miami"),("Julián Álvarez","Forward","Atlético Madrid"),("Rodrigo De Paul","Midfielder","Atlético Madrid"),("Emiliano Martínez","Goalkeeper","Aston Villa"),("Enzo Fernández","Midfielder","Chelsea")],
    "France":      [("Kylian Mbappé","Forward","Real Madrid"),("Antoine Griezmann","Forward","Atlético Madrid"),("Aurélien Tchouaméni","Midfielder","Real Madrid"),("Mike Maignan","Goalkeeper","AC Milan"),("Warren Zaïre-Emery","Midfielder","PSG")],
    "Brazil":      [("Vinícius Jr.","Forward","Real Madrid"),("Rodrygo","Forward","Real Madrid"),("Endrick","Forward","Real Madrid"),("Alisson","Goalkeeper","Liverpool"),("Bruno Guimarães","Midfielder","Newcastle")],
    "England":     [("Harry Kane","Forward","Bayern Munich"),("Jude Bellingham","Midfielder","Real Madrid"),("Bukayo Saka","Forward","Arsenal"),("Phil Foden","Midfielder","Man City"),("Jordan Pickford","Goalkeeper","Everton")],
    "Spain":       [("Lamine Yamal","Forward","Barcelona"),("Pedri","Midfielder","Barcelona"),("Rodri","Midfielder","Man City"),("Álvaro Morata","Forward","AC Milan"),("Unai Simón","Goalkeeper","Athletic Club")],
    "Germany":     [("Florian Wirtz","Midfielder","Bayer Leverkusen"),("Jamal Musiala","Midfielder","Bayern Munich"),("Kai Havertz","Forward","Arsenal"),("Manuel Neuer","Goalkeeper","Bayern Munich"),("Joshua Kimmich","Midfielder","Bayern Munich")],
    "Portugal":    [("Cristiano Ronaldo","Forward","Al Nassr"),("Bruno Fernandes","Midfielder","Man United"),("Rúben Dias","Defender","Man City"),("Vitinha","Midfielder","PSG"),("Rafael Leão","Forward","AC Milan")],
    "Netherlands": [("Virgil van Dijk","Defender","Liverpool"),("Memphis Depay","Forward","Atlético Madrid"),("Xavi Simons","Midfielder","RB Leipzig"),("Cody Gakpo","Forward","Liverpool"),("Tijjani Reijnders","Midfielder","AC Milan")],
    "Belgium":     [("Romelu Lukaku","Forward","Napoli"),("Kevin De Bruyne","Midfielder","Man City"),("Thibaut Courtois","Goalkeeper","Real Madrid"),("Dodi Lukebakio","Forward","Sevilla"),("Axel Witsel","Midfielder","Atlético Madrid")],
    "Morocco":     [("Achraf Hakimi","Defender","PSG"),("Hakim Ziyech","Forward","Galatasaray"),("Youssef En-Nesyri","Forward","Fenerbahçe"),("Sofyan Amrabat","Midfielder","Fiorentina"),("Bilal El Khannouss","Midfielder","Genk")],
    "United States":[("Christian Pulisic","Forward","AC Milan"),("Tyler Adams","Midfielder","Bournemouth"),("Weston McKennie","Midfielder","Juventus"),("Ricardo Pepi","Forward","PSV"),("Matt Turner","Goalkeeper","Crystal Palace")],
    "Mexico":      [("Hirving Lozano","Forward","PSV"),("Guillermo Ochoa","Goalkeeper","Club América"),("Edson Álvarez","Midfielder","West Ham"),("Santiago Giménez","Forward","AC Milan"),("César Montes","Defender","Espanyol")],
    "Canada":      [("Alphonso Davies","Defender","Bayern Munich"),("Jonathan David","Forward","Lille"),("Tajon Buchanan","Forward","Inter Milan"),("Milan Borjan","Goalkeeper","Red Star Belgrade"),("Ismaël Koné","Midfielder","Marseille")],
    "Japan":       [("Takefusa Kubo","Forward","Real Sociedad"),("Ritsu Doan","Forward","SC Freiburg"),("Wataru Endo","Midfielder","Liverpool"),("Shuichi Gonda","Goalkeeper","Shimizu S-Pulse"),("Hidemasa Morita","Midfielder","Sporting CP")],
    "South Korea": [("Son Heung-min","Forward","LAFC"),("Lee Kang-in","Midfielder","PSG"),("Kim Min-jae","Defender","Bayern Munich"),("Cho Gue-sung","Forward","Midtjylland"),("Hwang Hee-chan","Forward","Wolves")],
    "Australia":   [("Mathew Ryan","Goalkeeper","AZ Alkmaar"),("Mathew Leckie","Forward","Melbourne City"),("Jackson Irvine","Midfielder","St. Pauli"),("Harry Souttar","Defender","Leicester"),("Nestory Irankunda","Forward","Bayern Munich")],
    "Senegal":     [("Sadio Mané","Forward","Al Nassr"),("Édouard Mendy","Goalkeeper","Al Ahli"),("Kalidou Koulibaly","Defender","Al Hilal"),("Idrissa Gueye","Midfielder","Everton"),("Ismaïla Sarr","Forward","Crystal Palace")],
    "Uruguay":     [("Federico Valverde","Midfielder","Real Madrid"),("Darwin Núñez","Forward","Liverpool"),("Ronald Araújo","Defender","Barcelona"),("Rodrigo Bentancur","Midfielder","Tottenham"),("José María Giménez","Defender","Atlético Madrid")],
    "Colombia":    [("James Rodríguez","Midfielder","Rayo Vallecano"),("Luis Díaz","Forward","Liverpool"),("Davinson Sánchez","Defender","Galatasaray"),("Richard Ríos","Midfielder","Palmeiras"),("Juan Cuadrado","Forward","Inter Miami")],
    "Ecuador":     [("Moisés Caicedo","Midfielder","Chelsea"),("Enner Valencia","Forward","LDU Quito"),("Piero Hincapié","Defender","Bayer Leverkusen"),("Jeremy Sarmiento","Forward","Brighton"),("Gonzalo Plata","Forward","Valladolid")],
    "Switzerland": [("Granit Xhaka","Midfielder","Bayer Leverkusen"),("Xherdan Shaqiri","Forward","Chicago Fire"),("Manuel Akanji","Defender","Man City"),("Breel Embolo","Forward","Monaco"),("Yann Sommer","Goalkeeper","Inter Milan")],
    "Croatia":     [("Luka Modrić","Midfielder","Real Madrid"),("Ivan Perišić","Forward","Hajduk Split"),("Mateo Kovačić","Midfielder","Man City"),("Dominik Livaković","Goalkeeper","Fenerbahçe"),("Joško Gvardiol","Defender","Man City")],
    "Iran":        [("Sardar Azmoun","Forward","Bayer Leverkusen"),("Alireza Jahanbakhsh","Forward","Feyenoord"),("Mehdi Taremi","Forward","Inter Milan"),("Ali Beiranvand","Goalkeeper","Persepolis"),("Saman Ghoddos","Midfielder","Brentford")],
    "Saudi Arabia":[("Salem Al-Dawsari","Forward","Al Hilal"),("Mohammed Al-Owais","Goalkeeper","Al Hilal"),("Saud Abdulhamid","Defender","Roma"),("Firas Al-Buraikan","Forward","Al Fateh"),("Saleh Al-Shehri","Forward","Al Hilal")],
    "Ghana":       [("Jordan Ayew","Forward","Crystal Palace"),("Thomas Partey","Midfielder","Arsenal"),("André Ayew","Forward","Le Havre"),("Mohammed Kudus","Forward","West Ham"),("Lawrence Ati-Zigi","Goalkeeper","St. Gallen")],
    "Ivory Coast": [("Sébastien Haller","Forward","Dortmund"),("Franck Kessié","Midfielder","Barcelona"),("Serge Aurier","Defender","Villarreal"),("Wilfried Zaha","Forward","Galatasaray"),("Maxwel Cornet","Forward","Southampton")],
    "Egypt":       [("Mohamed Salah","Forward","Liverpool"),("Mohamed El Shenawy","Goalkeeper","Al Ahly"),("Ahmed Hegazy","Defender","Al Ittihad"),("Trezeguet","Forward","Istanbul Başakşehir"),("Amr El Sulaya","Midfielder","Al Ahly")],
    "Scotland":    [("Andrew Robertson","Defender","Liverpool"),("Scott McTominay","Midfielder","Napoli"),("Kieran Tierney","Defender","Real Sociedad"),("Angus Gunn","Goalkeeper","Norwich"),("John McGinn","Midfielder","Aston Villa")],
    "Turkey":      [("Hakan Çalhanoğlu","Midfielder","Inter Milan"),("Arda Güler","Midfielder","Real Madrid"),("Kenan Yıldız","Forward","Juventus"),("Çağlar Söyüncü","Defender","Atlético Madrid"),("Mert Günok","Goalkeeper","Beşiktaş")],
    "Austria":     [("David Alaba","Defender","Real Madrid"),("Marcel Sabitzer","Midfielder","Dortmund"),("Marko Arnautović","Forward","Man United"),("Konrad Laimer","Midfielder","Bayern Munich"),("Patrick Pentz","Goalkeeper","Bayer Leverkusen")],
    "Sweden":      [("Alexander Isak","Forward","Newcastle"),("Viktor Gyökeres","Forward","Sporting CP"),("Dejan Kulusevski","Forward","Tottenham"),("Emil Forsberg","Midfielder","New York RB"),("Victor Lindelöf","Defender","Man United")],
    "Paraguay":    [("Miguel Almirón","Midfielder","Newcastle"),("Matías Villasanti","Midfielder","Grêmio"),("Gustavo Gómez","Defender","Palmeiras"),("Antony Silva","Goalkeeper","Olimpia"),("Antonio Sanabria","Forward","Torino")],
    "Norway":      [("Erling Haaland","Forward","Man City"),("Martin Ødegaard","Midfielder","Arsenal"),("Alexander Sørloth","Forward","Atlético Madrid"),("Sander Berge","Midfielder","Burnley"),("Ørjan Nyland","Goalkeeper","Southampton")],
    "Algeria":     [("Riyad Mahrez","Forward","Al Ahli"),("Ismaël Bennacer","Midfielder","AC Milan"),("Youcef Atal","Defender","Nice"),("Andy Delort","Forward","Nice"),("Aïssa Mandi","Defender","Villarreal")],
    "New Zealand": [("Chris Wood","Forward","Nottingham Forest"),("Clayton Lewis","Midfielder","Club Brugge"),("Bill Tuilagi","Forward","Adelaide United"),("Finn Surman","Midfielder","Real Madrid"),("Max Crocombe","Goalkeeper","Celta Vigo")],
    "Qatar":       [("Akram Afif","Forward","Al Sadd"),("Almoez Ali","Forward","Al Duhail"),("Hassan Al-Haydos","Midfielder","Al Sadd"),("Meshaal Barsham","Goalkeeper","Al Sadd"),("Boualem Khoukhi","Defender","Al Sadd")],
    "Cape Verde":  [("Gelson Martins","Forward","Monaco"),("Garry Rodrigues","Forward","Galatasaray"),("Ryan Mendes","Forward","Lille"),("Júnior Alves","Midfielder","Arouca"),("Vozinha","Goalkeeper","Celta Vigo")],
    "Iraq":        [("Aymen Hussein","Forward","Al Zawraa"),("Amjed Attwan","Midfielder","Al Shorta"),("Dundar Mawlood","Goalkeeper","Erbil SC"),("Ali Adnan","Defender","Deportivo La Coruña"),("Ahmed Yasin","Midfielder","Al Zawraa")],
    "Jordan":      [("Yazan Al-Naimat","Forward","Al Faisaly"),("Ahmad Haikal","Midfielder","Shabab Al Ordun"),("Hamza Aldarawsheh","Midfielder","Al Ain"),("Mohamad Abu Laila","Defender","Swarovski Tirol"),("Zaid Abu Laila","Forward","Hapoel Haifa")],
    "Uzbekistan":  [("Abdukodir Khusanov","Defender","Man City"),("Eldor Shomurodov","Forward","Roma"),("Jaloliddin Masharipov","Forward","Al Nojoom"),("Otabek Shukurov","Midfielder","Pakhtakor"),("Hamza Kamolov","Midfielder","Pakhtakor")],
    "DR Congo":    [("Cédric Bakambu","Forward","Marseille"),("Chancel Mbemba","Defender","Marseille"),("Arthur Masuaku","Defender","Besiktas"),("Silas","Forward","VfB Stuttgart"),("Gaël Kakuta","Midfielder","Amiens")],
    "Tunisia":     [("Wahbi Khazri","Forward","Montpellier"),("Youssef Msakni","Forward","Al Arabi"),("Hannibal Mejbri","Midfielder","Burnley"),("Aymen Dahmen","Goalkeeper","SC Freiburg"),("Ali Maâloul","Defender","Al Ahly")],
    "Haiti":       [("Nazon","Forward","Charlotte FC"),("Mechack Jérôme","Defender","Pittsburgh Riverhounds"),("Kervens Belfort","Midfielder","FC Metz"),("Duckens Nazon","Forward","Sochaux"),("Frantzdy Pierrot","Forward","Cincinnati")],
    "Panama":      [("Rolando Blackburn","Forward","Nottm Forest"),("Roderick Miller","Midfielder","Sporting KC"),("Anibal Godoy","Midfielder","Nashville SC"),("Orlando Mosquera","Goalkeeper","FC Dallas"),("Adalberto Carrasquilla","Midfielder","Hartford Athletic")],
    "Bosnia and Herzegovina":[("Edin Džeko","Forward","Fenerbahçe"),("Miralem Pjanić","Midfielder","Sharjah"),("Aleksandar Đorđević","Defender","Sparta Prague"),("Nikola Jurčević","Goalkeeper","Dinamo Zagreb"),("Vedran Ćorluka","Defender","Lokomotiv Moscow")],
    "Curacao":     [("Juriën Timber","Defender","Arsenal"),("Leandro Bacuna","Midfielder","Cardiff City"),("Cuco Martina","Defender","Stoke City"),("Quentin Boisgard","Forward","Nantes"),("Elson Hooi","Forward","ADO Den Haag")],
    "Czechia":     [("Patrik Schick","Forward","Bayer Leverkusen"),("Tomáš Souček","Midfielder","West Ham"),("Adam Hložek","Forward","Hoffenheim"),("Antonín Barák","Midfielder","Fiorentina"),("Vladimír Coufal","Defender","West Ham")],
    "South Africa":[("Percy Tau","Forward","Al Ahly"),("Ronwen Williams","Goalkeeper","Mamelodi Sundowns"),("Teboho Mokoena","Midfielder","Mamelodi Sundowns"),("Lyle Foster","Forward","Burnley"),("Mothobi Mvala","Defender","Mamelodi Sundowns")],
    "Scotland":    [("Andrew Robertson","Defender","Liverpool"),("Scott McTominay","Midfielder","Napoli"),("Kieran Tierney","Defender","Real Sociedad"),("Angus Gunn","Goalkeeper","Norwich"),("John McGinn","Midfielder","Aston Villa")],
}

def flag(team):
    return FLAGS.get(normalize_team_name(team), "🏳️")


def _html_cell(value):
    return html.escape(str(value))


def render_metric_card(label, value, delta=""):
    delta_html = f"<div class='dashboard-metric-delta'>{_html_cell(delta)}</div>" if delta else ""
    return f"""
    <div class='dashboard-metric'>
        <div class='dashboard-metric-label'>{_html_cell(label)}</div>
        <div class='dashboard-metric-value'>{_html_cell(value)}</div>
        {delta_html}
    </div>
    """


def render_centered_table(df, hide_index=False):
    columns = list(df.columns)
    headers = columns if hide_index else [""] + columns
    header_html = "".join(f"<th>{_html_cell(header)}</th>" for header in headers)
    row_html = []

    for index, row in df.iterrows():
        cells = []
        if not hide_index:
            cells.append(f"<td>{_html_cell(index)}</td>")
        cells.extend(f"<td>{_html_cell(row[column])}</td>" for column in columns)
        row_html.append(f"<tr>{''.join(cells)}</tr>")

    return f"""
    <div class='centered-table-wrap'>
        <table class='centered-table'>
            <thead><tr>{header_html}</tr></thead>
            <tbody>{''.join(row_html)}</tbody>
        </table>
    </div>
    """

# ── GROUP COLORS ─────────────────────────────────────────────────────────────
GROUP_COLORS = {
    "A": "#FF6B6B", "B": "#FF9F43", "C": "#F7C948",
    "D": "#48D8A0", "E": "#48C9F7", "F": "#748CF7",
    "G": "#C874F7", "H": "#F774C8", "I": "#74F7E8", "J": "#F79F74",
    "K": "#A8F774", "L": "#F77474",
}

STANDINGS_LEGEND_HTML = """
<div class='standings-legend'>
    <span><strong>P</strong> = Played</span>
    <span><strong>W</strong> = Wins</span>
    <span><strong>D</strong> = Draws</span>
    <span><strong>L</strong> = Losses</span>
    <span><strong>GF</strong> = Goals For</span>
    <span><strong>GA</strong> = Goals Against</span>
    <span><strong>GD</strong> = Goal Difference</span>
    <span><strong>Pts</strong> = Points</span>
</div>
"""

# ── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide Streamlit toolbar, hamburger menu, footer, GitHub link, Manage app */
#MainMenu {visibility: hidden !important; display: none !important;}
header[data-testid="stHeader"] {visibility: hidden !important; display: none !important;}
footer {visibility: hidden !important; display: none !important;}
[data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stDeployButton {display: none !important;}
a[href*="github"] {display: none !important;}
.viewerBadge_container__r5tak {display: none !important;}
.viewerBadge_link__qRIco {display: none !important;}
#stDecoration {display: none !important;}
button[kind="header"] {display: none !important;}
[data-testid="manage-app-button"] {display: none !important;}
iframe[title="streamlit_analytics"] {display: none !important;}
div[class*="StatusWidget"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

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

.dashboard-metric { text-align:center; width:100%; padding:0.35rem 0; }
.dashboard-metric-label {
    color:#8a9ab5;
    font-size:0.8rem;
    font-weight:700;
    text-transform:uppercase;
    letter-spacing:1px;
}
.dashboard-metric-value {
    font-family:'Bebas Neue', sans-serif !important;
    font-size:2.35rem;
    line-height:1.05;
    color:#F7C948;
    text-align:center;
}
.dashboard-metric-delta {
    color:#8a9ab5;
    font-size:0.8rem;
    text-align:center;
}
.centered-table-wrap {
    width:100%;
    overflow-x:auto;
    border:1px solid #252d45;
    border-radius:10px;
    background:#101520;
}
.centered-table {
    width:100%;
    border-collapse:collapse;
    table-layout:auto;
}
.centered-table th, .centered-table td {
    text-align:center;
    vertical-align:middle;
    padding:0.75rem 0.8rem;
    border-bottom:1px solid #252d45;
    border-right:1px solid #252d45;
    color:#e8eaf0;
}
.centered-table th {
    color:#8a9ab5;
    font-weight:700;
    background:#1a1d26;
}
.centered-table th:last-child, .centered-table td:last-child { border-right:none; }
.centered-table tr:last-child td { border-bottom:none; }
.standings-legend {
    display:flex;
    flex-wrap:wrap;
    justify-content:center;
    gap:0.45rem 1rem;
    color:#8a9ab5;
    font-size:0.85rem;
    text-align:center;
    margin:0.25rem 0 1rem;
}
.standings-legend strong { color:#F7C948; }

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
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# ── MATCH FILE ───────────────────────────────────────────────────────────────
MATCH_FILE = Path("matches.csv")

MATCH_START_TIMES_ET = {
    ("2026-06-11", "Mexico", "South Africa"): "3:00 PM ET",
    ("2026-06-11", "South Korea", "Czechia"): "10:00 PM ET",
    ("2026-06-18", "Mexico", "South Korea"): "9:00 PM ET",
    ("2026-06-18", "Czechia", "South Africa"): "12:00 PM ET",
    ("2026-06-24", "South Africa", "South Korea"): "9:00 PM ET",
    ("2026-06-24", "Czechia", "Mexico"): "9:00 PM ET",
    ("2026-06-12", "Canada", "Bosnia and Herzegovina"): "3:00 PM ET",
    ("2026-06-13", "Qatar", "Switzerland"): "3:00 PM ET",
    ("2026-06-18", "Switzerland", "Bosnia and Herzegovina"): "3:00 PM ET",
    ("2026-06-18", "Canada", "Qatar"): "6:00 PM ET",
    ("2026-06-24", "Switzerland", "Canada"): "3:00 PM ET",
    ("2026-06-24", "Bosnia and Herzegovina", "Qatar"): "3:00 PM ET",
    ("2026-06-13", "Brazil", "Morocco"): "6:00 PM ET",
    ("2026-06-13", "Haiti", "Scotland"): "9:00 PM ET",
    ("2026-06-19", "Scotland", "Morocco"): "6:00 PM ET",
    ("2026-06-19", "Brazil", "Haiti"): "9:00 PM ET",
    ("2026-06-24", "Scotland", "Brazil"): "6:00 PM ET",
    ("2026-06-24", "Morocco", "Haiti"): "6:00 PM ET",
    ("2026-06-12", "United States", "Paraguay"): "9:00 PM ET",
    ("2026-06-13", "Australia", "Turkey"): "12:00 AM ET",
    ("2026-06-19", "United States", "Australia"): "3:00 PM ET",
    ("2026-06-19", "Turkey", "Paraguay"): "11:00 PM ET",
    ("2026-06-25", "Turkey", "United States"): "10:00 PM ET",
    ("2026-06-25", "Paraguay", "Australia"): "10:00 PM ET",
    ("2026-06-14", "Germany", "Curacao"): "1:00 PM ET",
    ("2026-06-14", "Ivory Coast", "Ecuador"): "7:00 PM ET",
    ("2026-06-20", "Germany", "Ivory Coast"): "4:00 PM ET",
    ("2026-06-20", "Ecuador", "Curacao"): "8:00 PM ET",
    ("2026-06-25", "Ecuador", "Germany"): "4:00 PM ET",
    ("2026-06-25", "Curacao", "Ivory Coast"): "4:00 PM ET",
    ("2026-06-14", "Netherlands", "Japan"): "4:00 PM ET",
    ("2026-06-14", "Sweden", "Tunisia"): "10:00 PM ET",
    ("2026-06-20", "Netherlands", "Sweden"): "1:00 PM ET",
    ("2026-06-20", "Tunisia", "Japan"): "12:00 AM ET",
    ("2026-06-25", "Japan", "Sweden"): "7:00 PM ET",
    ("2026-06-25", "Tunisia", "Netherlands"): "7:00 PM ET",
    ("2026-06-15", "Belgium", "Egypt"): "3:00 PM ET",
    ("2026-06-15", "Iran", "New Zealand"): "9:00 PM ET",
    ("2026-06-21", "Belgium", "Iran"): "3:00 PM ET",
    ("2026-06-21", "New Zealand", "Egypt"): "9:00 PM ET",
    ("2026-06-26", "Egypt", "Iran"): "11:00 PM ET",
    ("2026-06-26", "New Zealand", "Belgium"): "11:00 PM ET",
    ("2026-06-15", "Spain", "Cape Verde"): "12:00 PM ET",
    ("2026-06-15", "Saudi Arabia", "Uruguay"): "6:00 PM ET",
    ("2026-06-21", "Spain", "Saudi Arabia"): "12:00 PM ET",
    ("2026-06-21", "Uruguay", "Cape Verde"): "6:00 PM ET",
    ("2026-06-26", "Cape Verde", "Saudi Arabia"): "8:00 PM ET",
    ("2026-06-26", "Uruguay", "Spain"): "8:00 PM ET",
    ("2026-06-16", "France", "Senegal"): "3:00 PM ET",
    ("2026-06-16", "Iraq", "Norway"): "6:00 PM ET",
    ("2026-06-22", "France", "Iraq"): "5:00 PM ET",
    ("2026-06-22", "Norway", "Senegal"): "8:00 PM ET",
    ("2026-06-26", "Norway", "France"): "3:00 PM ET",
    ("2026-06-26", "Senegal", "Iraq"): "3:00 PM ET",
    ("2026-06-16", "Argentina", "Algeria"): "9:00 PM ET",
    ("2026-06-16", "Austria", "Jordan"): "12:00 AM ET",
    ("2026-06-22", "Argentina", "Austria"): "1:00 PM ET",
    ("2026-06-22", "Jordan", "Algeria"): "11:00 PM ET",
    ("2026-06-27", "Algeria", "Austria"): "10:00 PM ET",
    ("2026-06-27", "Jordan", "Argentina"): "10:00 PM ET",
    ("2026-06-17", "Portugal", "DR Congo"): "1:00 PM ET",
    ("2026-06-17", "Uzbekistan", "Colombia"): "10:00 PM ET",
    ("2026-06-23", "Portugal", "Uzbekistan"): "1:00 PM ET",
    ("2026-06-23", "Colombia", "DR Congo"): "10:00 PM ET",
    ("2026-06-27", "Colombia", "Portugal"): "7:30 PM ET",
    ("2026-06-27", "DR Congo", "Uzbekistan"): "7:30 PM ET",
    ("2026-06-17", "England", "Croatia"): "4:00 PM ET",
    ("2026-06-17", "Ghana", "Panama"): "7:00 PM ET",
    ("2026-06-23", "England", "Ghana"): "4:00 PM ET",
    ("2026-06-23", "Panama", "Croatia"): "7:00 PM ET",
    ("2026-06-27", "Panama", "England"): "5:00 PM ET",
    ("2026-06-27", "Croatia", "Ghana"): "5:00 PM ET",
}

DEFAULT_MATCHES = pd.DataFrame([
    # ── GROUP A ──────────────────────────────────────────────────────────────
    {"Match ID": 1,  "Group": "A", "Date": "2026-06-11", "Team A": "Mexico",       "Team B": "South Africa", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Mexico City Stadium"},
    {"Match ID": 2,  "Group": "A", "Date": "2026-06-11", "Team A": "South Korea",  "Team B": "Czechia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Guadalajara"},
    {"Match ID": 3,  "Group": "A", "Date": "2026-06-18", "Team A": "Mexico",       "Team B": "South Korea",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Guadalajara"},
    {"Match ID": 4,  "Group": "A", "Date": "2026-06-18", "Team A": "Czechia",      "Team B": "South Africa", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Atlanta Stadium"},
    {"Match ID": 5,  "Group": "A", "Date": "2026-06-24", "Team A": "South Africa", "Team B": "South Korea",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Monterrey"},
    {"Match ID": 6,  "Group": "A", "Date": "2026-06-24", "Team A": "Czechia",      "Team B": "Mexico",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Mexico City Stadium"},
    # ── GROUP B ──────────────────────────────────────────────────────────────
    {"Match ID": 7,  "Group": "B", "Date": "2026-06-12", "Team A": "Canada",       "Team B": "Bosnia and Herzegovina", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Toronto Stadium"},
    {"Match ID": 8,  "Group": "B", "Date": "2026-06-13", "Team A": "Qatar",        "Team B": "Switzerland",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "San Francisco Bay Area Stadium"},
    {"Match ID": 9,  "Group": "B", "Date": "2026-06-18", "Team A": "Switzerland",  "Team B": "Bosnia and Herzegovina", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Los Angeles Stadium"},
    {"Match ID": 10, "Group": "B", "Date": "2026-06-18", "Team A": "Canada",       "Team B": "Qatar",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "BC Place"},
    {"Match ID": 11, "Group": "B", "Date": "2026-06-24", "Team A": "Switzerland",  "Team B": "Canada",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "BC Place"},
    {"Match ID": 12, "Group": "B", "Date": "2026-06-24", "Team A": "Bosnia and Herzegovina", "Team B": "Qatar", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Seattle Stadium"},
    # ── GROUP C ──────────────────────────────────────────────────────────────
    {"Match ID": 13, "Group": "C", "Date": "2026-06-13", "Team A": "Brazil",       "Team B": "Morocco",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "New York New Jersey Stadium"},
    {"Match ID": 14, "Group": "C", "Date": "2026-06-13", "Team A": "Haiti",        "Team B": "Scotland",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Boston Stadium"},
    {"Match ID": 15, "Group": "C", "Date": "2026-06-19", "Team A": "Scotland",     "Team B": "Morocco",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Boston Stadium"},
    {"Match ID": 16, "Group": "C", "Date": "2026-06-19", "Team A": "Brazil",       "Team B": "Haiti",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Philadelphia Stadium"},
    {"Match ID": 17, "Group": "C", "Date": "2026-06-24", "Team A": "Scotland",     "Team B": "Brazil",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Miami Stadium"},
    {"Match ID": 18, "Group": "C", "Date": "2026-06-24", "Team A": "Morocco",      "Team B": "Haiti",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Atlanta Stadium"},
    # ── GROUP D ──────────────────────────────────────────────────────────────
    {"Match ID": 19, "Group": "D", "Date": "2026-06-12", "Team A": "United States","Team B": "Paraguay",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Los Angeles Stadium"},
    {"Match ID": 20, "Group": "D", "Date": "2026-06-13", "Team A": "Australia",    "Team B": "Turkey",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "BC Place"},
    {"Match ID": 21, "Group": "D", "Date": "2026-06-19", "Team A": "United States","Team B": "Australia",    "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Seattle Stadium"},
    {"Match ID": 22, "Group": "D", "Date": "2026-06-19", "Team A": "Turkey",       "Team B": "Paraguay",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "San Francisco Bay Area Stadium"},
    {"Match ID": 23, "Group": "D", "Date": "2026-06-25", "Team A": "Turkey",       "Team B": "United States","Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Los Angeles Stadium"},
    {"Match ID": 24, "Group": "D", "Date": "2026-06-25", "Team A": "Paraguay",     "Team B": "Australia",    "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "San Francisco Bay Area Stadium"},
    # ── GROUP E ──────────────────────────────────────────────────────────────
    {"Match ID": 25, "Group": "E", "Date": "2026-06-14", "Team A": "Germany",      "Team B": "Curacao",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Houston Stadium"},
    {"Match ID": 26, "Group": "E", "Date": "2026-06-14", "Team A": "Ivory Coast",  "Team B": "Ecuador",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Philadelphia Stadium"},
    {"Match ID": 27, "Group": "E", "Date": "2026-06-20", "Team A": "Germany",      "Team B": "Ivory Coast",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Toronto Stadium"},
    {"Match ID": 28, "Group": "E", "Date": "2026-06-20", "Team A": "Ecuador",      "Team B": "Curacao",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Kansas City Stadium"},
    {"Match ID": 29, "Group": "E", "Date": "2026-06-25", "Team A": "Ecuador",      "Team B": "Germany",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "New York New Jersey Stadium"},
    {"Match ID": 30, "Group": "E", "Date": "2026-06-25", "Team A": "Curacao",      "Team B": "Ivory Coast",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Philadelphia Stadium"},
    # ── GROUP F ──────────────────────────────────────────────────────────────
    {"Match ID": 31, "Group": "F", "Date": "2026-06-14", "Team A": "Netherlands",  "Team B": "Japan",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Dallas Stadium"},
    {"Match ID": 32, "Group": "F", "Date": "2026-06-14", "Team A": "Sweden",       "Team B": "Tunisia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Monterrey"},
    {"Match ID": 33, "Group": "F", "Date": "2026-06-20", "Team A": "Netherlands",  "Team B": "Sweden",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Houston Stadium"},
    {"Match ID": 34, "Group": "F", "Date": "2026-06-20", "Team A": "Tunisia",      "Team B": "Japan",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Monterrey"},
    {"Match ID": 35, "Group": "F", "Date": "2026-06-25", "Team A": "Japan",        "Team B": "Sweden",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Dallas Stadium"},
    {"Match ID": 36, "Group": "F", "Date": "2026-06-25", "Team A": "Tunisia",      "Team B": "Netherlands",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Kansas City Stadium"},
    # ── GROUP G ──────────────────────────────────────────────────────────────
    {"Match ID": 37, "Group": "G", "Date": "2026-06-15", "Team A": "Belgium",      "Team B": "Egypt",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Seattle Stadium"},
    {"Match ID": 38, "Group": "G", "Date": "2026-06-15", "Team A": "Iran",         "Team B": "New Zealand",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Los Angeles Stadium"},
    {"Match ID": 39, "Group": "G", "Date": "2026-06-21", "Team A": "Belgium",      "Team B": "Iran",         "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Los Angeles Stadium"},
    {"Match ID": 40, "Group": "G", "Date": "2026-06-21", "Team A": "New Zealand",  "Team B": "Egypt",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "BC Place"},
    {"Match ID": 41, "Group": "G", "Date": "2026-06-26", "Team A": "Egypt",        "Team B": "Iran",         "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Seattle Stadium"},
    {"Match ID": 42, "Group": "G", "Date": "2026-06-26", "Team A": "New Zealand",  "Team B": "Belgium",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "BC Place"},
    # ── GROUP H ──────────────────────────────────────────────────────────────
    {"Match ID": 43, "Group": "H", "Date": "2026-06-15", "Team A": "Spain",        "Team B": "Cape Verde",   "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Atlanta Stadium"},
    {"Match ID": 44, "Group": "H", "Date": "2026-06-15", "Team A": "Saudi Arabia", "Team B": "Uruguay",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Miami Stadium"},
    {"Match ID": 45, "Group": "H", "Date": "2026-06-21", "Team A": "Spain",        "Team B": "Saudi Arabia", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Atlanta Stadium"},
    {"Match ID": 46, "Group": "H", "Date": "2026-06-21", "Team A": "Uruguay",      "Team B": "Cape Verde",   "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Miami Stadium"},
    {"Match ID": 47, "Group": "H", "Date": "2026-06-26", "Team A": "Cape Verde",   "Team B": "Saudi Arabia", "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Houston Stadium"},
    {"Match ID": 48, "Group": "H", "Date": "2026-06-26", "Team A": "Uruguay",      "Team B": "Spain",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Guadalajara"},
    # ── GROUP I ──────────────────────────────────────────────────────────────
    {"Match ID": 49, "Group": "I", "Date": "2026-06-16", "Team A": "France",       "Team B": "Senegal",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "New York New Jersey Stadium"},
    {"Match ID": 50, "Group": "I", "Date": "2026-06-16", "Team A": "Iraq",         "Team B": "Norway",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Boston Stadium"},
    {"Match ID": 51, "Group": "I", "Date": "2026-06-22", "Team A": "France",       "Team B": "Iraq",         "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Philadelphia Stadium"},
    {"Match ID": 52, "Group": "I", "Date": "2026-06-22", "Team A": "Norway",       "Team B": "Senegal",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "New York New Jersey Stadium"},
    {"Match ID": 53, "Group": "I", "Date": "2026-06-26", "Team A": "Norway",       "Team B": "France",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Boston Stadium"},
    {"Match ID": 54, "Group": "I", "Date": "2026-06-26", "Team A": "Senegal",      "Team B": "Iraq",         "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Toronto Stadium"},
    # ── GROUP J ──────────────────────────────────────────────────────────────
    {"Match ID": 55, "Group": "J", "Date": "2026-06-16", "Team A": "Argentina",    "Team B": "Algeria",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Kansas City Stadium"},
    {"Match ID": 56, "Group": "J", "Date": "2026-06-16", "Team A": "Austria",      "Team B": "Jordan",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "San Francisco Bay Area Stadium"},
    {"Match ID": 57, "Group": "J", "Date": "2026-06-22", "Team A": "Argentina",    "Team B": "Austria",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Dallas Stadium"},
    {"Match ID": 58, "Group": "J", "Date": "2026-06-22", "Team A": "Jordan",       "Team B": "Algeria",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "San Francisco Bay Area Stadium"},
    {"Match ID": 59, "Group": "J", "Date": "2026-06-27", "Team A": "Algeria",      "Team B": "Austria",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Kansas City Stadium"},
    {"Match ID": 60, "Group": "J", "Date": "2026-06-27", "Team A": "Jordan",       "Team B": "Argentina",    "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Dallas Stadium"},
    # ── GROUP K ──────────────────────────────────────────────────────────────
    {"Match ID": 61, "Group": "K", "Date": "2026-06-17", "Team A": "Portugal",     "Team B": "DR Congo",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Houston Stadium"},
    {"Match ID": 62, "Group": "K", "Date": "2026-06-17", "Team A": "Uzbekistan",   "Team B": "Colombia",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Mexico City Stadium"},
    {"Match ID": 63, "Group": "K", "Date": "2026-06-23", "Team A": "Portugal",     "Team B": "Uzbekistan",   "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Houston Stadium"},
    {"Match ID": 64, "Group": "K", "Date": "2026-06-23", "Team A": "Colombia",     "Team B": "DR Congo",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Guadalajara"},
    {"Match ID": 65, "Group": "K", "Date": "2026-06-27", "Team A": "Colombia",     "Team B": "Portugal",     "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Miami Stadium"},
    {"Match ID": 66, "Group": "K", "Date": "2026-06-27", "Team A": "DR Congo",     "Team B": "Uzbekistan",   "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Atlanta Stadium"},
    # ── GROUP L ──────────────────────────────────────────────────────────────
    {"Match ID": 67, "Group": "L", "Date": "2026-06-17", "Team A": "England",      "Team B": "Croatia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Dallas Stadium"},
    {"Match ID": 68, "Group": "L", "Date": "2026-06-17", "Team A": "Ghana",        "Team B": "Panama",       "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Toronto Stadium"},
    {"Match ID": 69, "Group": "L", "Date": "2026-06-23", "Team A": "England",      "Team B": "Ghana",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Boston Stadium"},
    {"Match ID": 70, "Group": "L", "Date": "2026-06-23", "Team A": "Panama",       "Team B": "Croatia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Toronto Stadium"},
    {"Match ID": 71, "Group": "L", "Date": "2026-06-27", "Team A": "Panama",       "Team B": "England",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "New York New Jersey Stadium"},
    {"Match ID": 72, "Group": "L", "Date": "2026-06-27", "Team A": "Croatia",      "Team B": "Ghana",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Philadelphia Stadium"},
])

def load_matches():
    if MATCH_FILE.exists():
        return pd.read_csv(MATCH_FILE)
    return DEFAULT_MATCHES.copy()

def save_matches(df):
    df.to_csv(MATCH_FILE, index=False)

def default_match_time(match_row):
    key = (
        str(match_row.get("Date", "")).strip(),
        str(match_row.get("Team A", "")).strip(),
        str(match_row.get("Team B", "")).strip(),
    )
    return MATCH_START_TIMES_ET.get(key, "")

def ensure_columns(df):
    cols = ["Match ID", "Group", "Date", "Time", "Team A", "Team B", "Team A Score", "Team B Score", "Winner", "Loser", "Status", "Venue"]
    for c in cols:
        if c not in df.columns:
            df[c] = ""
    df["Time"] = df.apply(lambda r: default_match_time(r) or r["Time"], axis=1)
    return apply_known_final_results(df[cols].fillna(""), normalize_team_name)

def format_match_datetime(match_row):
    date = str(match_row.get("Date", "")).strip()
    time = str(match_row.get("Time", "")).strip()
    if date and time:
        return f"{date} · {time}"
    return date or time or "TBD"

def get_qualifiers(standings):
    if len(standings) == 0:
        return pd.DataFrame()
    top_two = standings.groupby("Group").head(2)
    thirds = standings.groupby("Group").nth(2).sort_values(["Pts", "GD", "GF"], ascending=[False, False, False]).head(8)
    return pd.concat([top_two, thirds], ignore_index=True)

def build_round_of_32(qualifiers):
    round_df = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES).copy()
    round_df["Match"] = [f"R32-{index + 1}" for index in range(len(round_df))]
    return round_df[["Match", "Match ID", "Team A", "Team B", "Status", "Winner"]]


def build_prediction_match_labels(match_catalog):
    match_labels = match_catalog.copy()
    round_titles = {"R32": "Round of 32", "R16": "Round of 16", "QF": "Quarterfinals"}
    match_labels["Round Order"] = match_labels["Group"].map({"R32": 0, "R16": 1, "QF": 2}).fillna(99)
    match_labels = match_labels.sort_values(["Round Order", "Match ID"]).copy()
    match_labels["Kickoff"] = match_labels["Group"].map(round_titles).fillna("")
    match_labels["Match"] = match_labels.apply(
        lambda r: f"{flag(r['Team A'])} {r['Team A']} vs {r['Team B']} {flag(r['Team B'])}", axis=1
    )
    return match_labels.drop(columns=["Round Order"])

def advance_round(prev_round_df):
    """Takes winners from a round and pairs them into the next round."""
    label_map = {"R32": "R16", "R16": "QF", "QF": "SF", "SF": "F"}
    prefix = prev_round_df["Match"].iloc[0].split("-")[0] if len(prev_round_df) else "R32"
    if prefix == "R32":
        return build_round_of_16_from_round_of_32(prev_round_df)

    winners = list(prev_round_df["Winner"].values)
    pairs = []
    next_prefix = label_map.get(prefix, "Next")
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            ta = winners[i] if winners[i] else f"Winner M{i+1}"
            tb = winners[i+1] if winners[i+1] else f"Winner M{i+2}"
            pairs.append({"Match": f"{next_prefix}-{i//2+1}", "Team A": ta, "Team B": tb, "Status": "Upcoming", "Winner": ""})
    return pd.DataFrame(pairs)

@st.cache_data(ttl=300)
def fetch_live_matches():
    if not API_KEY:
        return []
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/matches?status=LIVE", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("matches", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=300)
def fetch_todays_matches():
    if not API_KEY:
        return []
    try:
        today = today_et()
        r = requests.get(f"{API_BASE}/competitions/WC/matches?dateFrom={today}&dateTo={today}", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("matches", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=600)
def fetch_top_scorers():
    if not API_KEY:
        return []
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/scorers?limit=10", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("scorers", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=600)
def fetch_standings_api():
    if not API_KEY:
        return []
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/standings", headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json().get("standings", [])
    except Exception:
        pass
    return []


@st.cache_data(ttl=120)
def fetch_all_wc_matches():
    """Fetch all WC matches from API — used to auto-sync scores."""
    if not API_KEY:
        return []
    try:
        r = requests.get(f"{API_BASE}/competitions/WC/matches", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            return r.json().get("matches", [])
    except Exception:
        pass
    return []

def auto_sync_scores(matches_df):
    """Pull finished scores from API and update matches_df in place."""
    api_matches = fetch_all_wc_matches()
    if not api_matches:
        return matches_df, 0

    updated = matches_df.copy()
    count = 0

    for m in api_matches:
        status = m.get("status", "")
        if status not in ("FINISHED", "IN_PLAY", "PAUSED"):
            continue

        home = normalize_team_name(m["homeTeam"]["name"])
        away = normalize_team_name(m["awayTeam"]["name"])
        score = m.get("score", {})
        full = score.get("fullTime", {})
        home_score = full.get("home")
        away_score = full.get("away")

        if home_score is None or away_score is None:
            continue

        # Match by team names (try both orderings)
        team_a = updated["Team A"].map(normalize_team_name)
        team_b = updated["Team B"].map(normalize_team_name)
        mask = (
            ((team_a == home) & (team_b == away)) |
            ((team_a == away) & (team_b == home))
        )
        if not mask.any():
            continue

        idx = updated[mask].index[0]
        row = updated.loc[idx]

        # Flip scores if teams are reversed
        if normalize_team_name(row["Team A"]) == away:
            home_score, away_score = away_score, home_score

        # Only update if score changed
        if str(row["Team A Score"]) != str(home_score) or str(row["Team B Score"]) != str(away_score):
            updated.at[idx, "Team A Score"] = str(home_score)
            updated.at[idx, "Team B Score"] = str(away_score)
            if status == "FINISHED":
                updated.at[idx, "Status"] = "Finished"
            count += 1

    if count > 0:
        updated = updated.apply(compute_match_outcome, axis=1)
        save_matches(updated)

    return updated, count


def build_live_knockout_prediction_matches():
    columns = ["Match ID", "Group", "Date", "Time", "Team A", "Team B", "Team A Score", "Team B Score", "Winner", "Loser", "Status", "Venue"]
    api_matches = fetch_all_wc_matches()
    if not api_matches:
        return pd.DataFrame(columns=columns)

    rows = []
    for match in api_matches:
        if match.get("status") != "FINISHED":
            continue

        full_time = match.get("score", {}).get("fullTime", {})
        home_score = full_time.get("home")
        away_score = full_time.get("away")
        home_team = normalize_team_name(match.get("homeTeam", {}).get("name", ""))
        away_team = normalize_team_name(match.get("awayTeam", {}).get("name", ""))

        if not home_team or not away_team or home_score is None or away_score is None:
            continue

        rows.append(
            {
                "Match ID": "",
                "Group": "",
                "Date": str(match.get("utcDate", ""))[:10],
                "Time": "",
                "Team A": home_team,
                "Team B": away_team,
                "Team A Score": str(home_score),
                "Team B Score": str(away_score),
                "Winner": "",
                "Loser": "",
                "Status": "Finished",
                "Venue": "",
            }
        )

    if not rows:
        return pd.DataFrame(columns=columns)

    return pd.DataFrame(rows, columns=columns).apply(compute_match_outcome, axis=1)


def build_prediction_result_source(matches_df):
    live_knockout_matches = build_live_knockout_prediction_matches()
    if len(live_knockout_matches) == 0:
        return matches_df.copy()
    return pd.concat([matches_df, live_knockout_matches], ignore_index=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────

def refresh_prediction_scores(predictions, matches):
    active_predictions = filter_predictions_to_catalog(predictions, matches)
    scored = score_predictions(active_predictions, matches)
    if not scored.equals(predictions):
        save_predictions(scored)
    return scored

def get_leaderboard(predictions):
    if len(predictions) == 0:
        return pd.DataFrame()
    scored = predictions[predictions["Correct"].isin(["✅", "❌"])]
    if len(scored) == 0:
        return pd.DataFrame()
    lb = scored.groupby("Player").agg(
        Predicted=("Match ID", "count"),
        Correct=("Correct", lambda x: (x == "✅").sum()),
    ).reset_index()
    lb["Points"] = lb["Correct"] * 3
    lb["Accuracy"] = (lb["Correct"] / lb["Predicted"] * 100).round(1).astype(str) + "%"
    return lb.sort_values("Points", ascending=False).reset_index(drop=True)

if "predictions" not in st.session_state:
    st.session_state.predictions = load_predictions()

if "player_name" not in st.session_state:
    st.session_state.player_name = ""

if "matches" not in st.session_state:
    st.session_state.matches = ensure_columns(load_matches())

restore_bracket_store_if_missing(
    load_bracket(),
    should_seed=True,
    save_bracket_round_fn=save_bracket_round,
    load_bracket_fn=load_bracket,
    db_path=Path("predictions.sqlite3"),
)
repair_bracket_store_from_seed(
    load_bracket(),
    should_seed=True,
    save_bracket_round_fn=save_bracket_round,
    load_bracket_fn=load_bracket,
)

st.session_state.matches = ensure_columns(st.session_state.matches)
st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)

previous_lang = st.session_state.get("lang")
language_label = st.radio("Language / Idioma", list(LANGUAGES), horizontal=True, label_visibility="collapsed")
lang = LANGUAGES[language_label]
language_changed = previous_lang is not None and previous_lang != lang
st.session_state.lang = lang

# Auto-sync scores from API
if not language_changed:
    st.session_state.matches, synced_count = auto_sync_scores(st.session_state.matches)
    if synced_count > 0:
        st.toast(f"⚡ Auto-synced {synced_count} match score(s) from live API", icon="⚽")

standings = build_standings(st.session_state.matches)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
@keyframes trophyGlow { 0%,100%{filter:drop-shadow(0 0 6px #f7c94888)} 50%{filter:drop-shadow(0 0 18px #f7c948cc)} }
.block-container { padding-top:0.4rem !important; }
.spin-ball { display:inline-block; animation:spin 2s linear infinite; font-size:2.5rem; line-height:1; }
.trophy-img { animation:trophyGlow 3s ease-in-out infinite; }
.hero-shell { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0.35rem; padding:0 0 0.35rem; text-align:center; }
.hero-title-wrap { display:flex; flex-direction:column; align-items:center; text-align:center; gap:0.45rem; min-width:0; }
.hero-title-line { display:flex; align-items:center; justify-content:center; gap:1rem; }
.hero-title { font-size:clamp(2rem, 5vw, 3.5rem); margin:0; color:#F7C948; font-family:Bebas Neue,sans-serif; letter-spacing:3px; white-space:normal; overflow-wrap:normal; }
.hero-updated { color:#5a6a8a; margin:0; font-size:0.85rem; }
.trophy-img svg { width:clamp(110px, 14vw, 170px); height:auto; display:block; }
@media (max-width: 640px) {
    .hero-shell { align-items:center; gap:0.4rem; }
    .hero-title-wrap { gap:0.4rem; }
    .hero-title-line { gap:0.5rem; }
    .hero-title { font-size:2rem; line-height:0.95; letter-spacing:1px; max-width:12ch; }
    .hero-updated { font-size:0.72rem; }
    .spin-ball { font-size:1.35rem; }
    .trophy-img svg { width:78px; }
}
</style>
<div class='hero-shell'>
    <div class='trophy-img'><svg width="260" height="340" viewBox="0 0 680 580" role="img" xmlns="http://www.w3.org/2000/svg">
<defs>
  <linearGradient id="tg1" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" style="stop-color:#5a3c08"/>
    <stop offset="20%" style="stop-color:#c8960c"/>
    <stop offset="45%" style="stop-color:#ffe87c"/>
    <stop offset="55%" style="stop-color:#ffe87c"/>
    <stop offset="80%" style="stop-color:#c8960c"/>
    <stop offset="100%" style="stop-color:#5a3c08"/>
  </linearGradient>
  <linearGradient id="tg2" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" style="stop-color:#3a2a05"/>
    <stop offset="35%" style="stop-color:#d4a017"/>
    <stop offset="50%" style="stop-color:#f7c948"/>
    <stop offset="65%" style="stop-color:#d4a017"/>
    <stop offset="100%" style="stop-color:#3a2a05"/>
  </linearGradient>
  <linearGradient id="tgGreen" x1="0%" y1="0%" x2="100%" y2="0%">
    <stop offset="0%" style="stop-color:#0d200d"/>
    <stop offset="30%" style="stop-color:#1e5c1e"/>
    <stop offset="50%" style="stop-color:#2e8b2e"/>
    <stop offset="70%" style="stop-color:#1e5c1e"/>
    <stop offset="100%" style="stop-color:#0d200d"/>
  </linearGradient>
  <radialGradient id="tgGlobe" cx="40%" cy="35%" r="65%">
    <stop offset="0%" style="stop-color:#fff5b0"/>
    <stop offset="40%" style="stop-color:#f7c948"/>
    <stop offset="100%" style="stop-color:#7a5510"/>
  </radialGradient>
  <radialGradient id="tgShine" cx="30%" cy="25%" r="60%">
    <stop offset="0%" style="stop-color:#ffffff" stop-opacity="0.6"/>
    <stop offset="100%" style="stop-color:#ffffff" stop-opacity="0"/>
  </radialGradient>
</defs>
<ellipse cx="340" cy="530" rx="110" ry="12" fill="#000" opacity="0.25"/>
<rect x="228" y="500" width="224" height="20" rx="5" fill="url(#tgGreen)"/>
<rect x="232" y="502" width="216" height="6" rx="2" fill="#3aaa3a" opacity="0.3"/>
<line x1="232" y1="508" x2="448" y2="508" stroke="#1e5c1e" stroke-width="1" opacity="0.5"/>
<line x1="232" y1="512" x2="448" y2="512" stroke="#3aaa3a" stroke-width="0.5" opacity="0.3"/>
<line x1="232" y1="516" x2="448" y2="516" stroke="#1e5c1e" stroke-width="1" opacity="0.4"/>
<rect x="236" y="478" width="208" height="24" rx="4" fill="url(#tg2)"/>
<rect x="240" y="480" width="200" height="8" rx="2" fill="#ffe87c" opacity="0.15"/>
<line x1="244" y1="485" x2="436" y2="485" stroke="#5a3c08" stroke-width="0.5" opacity="0.6"/>
<line x1="244" y1="490" x2="436" y2="490" stroke="#5a3c08" stroke-width="0.5" opacity="0.4"/>
<line x1="244" y1="495" x2="436" y2="495" stroke="#5a3c08" stroke-width="0.5" opacity="0.6"/>
<rect x="252" y="460" width="176" height="20" rx="3" fill="url(#tg1)"/>
<rect x="256" y="462" width="168" height="6" rx="2" fill="#fff5b0" opacity="0.2"/>
<rect x="268" y="446" width="144" height="16" rx="3" fill="url(#tg2)"/>
<text x="340" y="458" text-anchor="middle" font-family="serif" font-size="9" fill="#5a3c08" font-weight="bold" opacity="0.8">FIFA WORLD CUP 2026</text>
<polygon points="296,446 312,362 368,362 384,446" fill="url(#tg1)"/>
<polygon points="332,446 336,362 344,362 348,446" fill="#fff5b0" opacity="0.25"/>
<polygon points="296,446 312,362 316,362 300,446" fill="#5a3c08" opacity="0.3"/>
<polygon points="380,446 368,362 372,362 384,446" fill="#5a3c08" opacity="0.3"/>
<ellipse cx="340" cy="364" rx="52" ry="14" fill="url(#tg2)"/>
<ellipse cx="340" cy="360" rx="52" ry="14" fill="url(#tg1)"/>
<ellipse cx="340" cy="356" rx="48" ry="11" fill="#ffe87c" opacity="0.2"/>
<polygon points="312,356 322,272 358,272 368,356" fill="url(#tg1)"/>
<polygon points="334,356 338,272 342,272 346,356" fill="#fff5b0" opacity="0.25"/>
<polygon points="312,356 322,272 326,272 316,356" fill="#5a3c08" opacity="0.25"/>
<polygon points="364,356 358,272 362,272 368,356" fill="#5a3c08" opacity="0.25"/>
<path d="M322,318 Q268,305 262,265 Q258,230 298,222 Q310,220 322,228" fill="none" stroke="#7a5510" stroke-width="16" stroke-linecap="round"/>
<path d="M322,318 Q268,305 262,265 Q258,230 298,222 Q310,220 322,228" fill="none" stroke="url(#tg1)" stroke-width="12" stroke-linecap="round"/>
<path d="M322,318 Q268,305 262,265 Q258,230 298,222 Q310,220 322,228" fill="none" stroke="#ffe87c" stroke-width="4" stroke-linecap="round" opacity="0.45"/>
<path d="M358,318 Q412,305 418,265 Q422,230 382,222 Q370,220 358,228" fill="none" stroke="#7a5510" stroke-width="16" stroke-linecap="round"/>
<path d="M358,318 Q412,305 418,265 Q422,230 382,222 Q370,220 358,228" fill="none" stroke="url(#tg1)" stroke-width="12" stroke-linecap="round"/>
<path d="M358,318 Q412,305 418,265 Q422,230 382,222 Q370,220 358,228" fill="none" stroke="#ffe87c" stroke-width="4" stroke-linecap="round" opacity="0.45"/>
<path d="M298,228 Q280,205 283,178 Q287,145 340,130 Q393,145 397,178 Q400,205 382,228 Z" fill="#5a3c08" opacity="0.4" transform="translate(3,3)"/>
<path d="M298,228 Q280,205 283,178 Q287,145 340,130 Q393,145 397,178 Q400,205 382,228 Z" fill="url(#tg1)"/>
<path d="M298,228 Q280,205 283,178 Q287,145 310,135 L315,145 Q296,158 294,178 Q292,202 308,222 Z" fill="#5a3c08" opacity="0.3"/>
<path d="M382,228 Q400,205 397,178 Q393,145 370,135 L365,145 Q384,158 386,178 Q388,202 372,222 Z" fill="#5a3c08" opacity="0.3"/>
<path d="M322,222 Q310,200 314,178 Q318,155 340,146 Q362,155 366,178 Q370,200 358,222 Z" fill="#fff5b0" opacity="0.2"/>
<circle cx="340" cy="112" r="58" fill="#f7c948" opacity="0.12"/>
<circle cx="343" cy="115" r="52" fill="#5a3c08" opacity="0.3"/>
<circle cx="340" cy="112" r="52" fill="url(#tgGlobe)"/>
<circle cx="340" cy="112" r="52" fill="url(#tgShine)"/>
<ellipse cx="340" cy="112" rx="52" ry="15" fill="none" stroke="#7a5510" stroke-width="0.8" opacity="0.45"/>
<ellipse cx="340" cy="90" rx="45" ry="10" fill="none" stroke="#7a5510" stroke-width="0.6" opacity="0.35"/>
<ellipse cx="340" cy="134" rx="45" ry="10" fill="none" stroke="#7a5510" stroke-width="0.6" opacity="0.35"/>
<path d="M340,60 Q360,88 360,112 Q360,136 340,164" fill="none" stroke="#7a5510" stroke-width="0.6" opacity="0.35"/>
<path d="M340,60 Q320,88 320,112 Q320,136 340,164" fill="none" stroke="#7a5510" stroke-width="0.6" opacity="0.35"/>
<path d="M300,90 Q308,82 318,85 Q322,92 318,100 Q310,105 302,98 Z" fill="#8B6914" opacity="0.55"/>
<path d="M312,108 Q318,105 322,112 Q320,122 314,126 Q308,122 309,114 Z" fill="#8B6914" opacity="0.5"/>
<path d="M335,82 Q342,78 348,83 Q350,90 346,95 Q340,97 335,92 Z" fill="#8B6914" opacity="0.5"/>
<path d="M336,100 Q344,97 350,104 Q352,116 346,122 Q338,124 334,116 Q332,108 336,100 Z" fill="#8B6914" opacity="0.5"/>
<path d="M352,82 Q366,78 374,85 Q378,95 372,102 Q362,106 354,100 Q348,92 352,82 Z" fill="#8B6914" opacity="0.5"/>
<path d="M362,116 Q370,113 374,118 Q374,126 368,128 Q362,126 360,120 Z" fill="#8B6914" opacity="0.45"/>
<circle cx="340" cy="112" r="52" fill="none" stroke="#c8960c" stroke-width="2"/>
<rect x="326" y="164" width="28" height="14" rx="3" fill="url(#tg1)"/>
<line x1="340" y1="52" x2="340" y2="36" stroke="#ffe87c" stroke-width="2.5" opacity="0.9" stroke-linecap="round"/>
<line x1="358" y1="56" x2="368" y2="42" stroke="#ffe87c" stroke-width="2" opacity="0.7" stroke-linecap="round"/>
<line x1="322" y1="56" x2="312" y2="42" stroke="#ffe87c" stroke-width="2" opacity="0.7" stroke-linecap="round"/>
<line x1="374" y1="68" x2="387" y2="58" stroke="#ffe87c" stroke-width="1.5" opacity="0.5" stroke-linecap="round"/>
<line x1="306" y1="68" x2="293" y2="58" stroke="#ffe87c" stroke-width="1.5" opacity="0.5" stroke-linecap="round"/>
<polygon points="340,26 343.5,36 354,36 345.5,42.5 348.5,53 340,46.5 331.5,53 334.5,42.5 326,36 336.5,36" fill="#ffe87c" opacity="0.95"/>
</svg></div>
    <div class='hero-title-wrap'>
        <div class='hero-title-line'>
            <span class='spin-ball'>⚽</span>
            <h1 class='hero-title'>FIFA WORLD CUP 2026</h1>
            <span class='spin-ball'>⚽</span>
        </div>
        <p class='hero-updated'>🔄 Updated """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </div>
</div>
""", unsafe_allow_html=True)

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
group_fixtures = len(st.session_state.matches)
groups = st.session_state.matches["Group"].nunique()
with m1:
    st.markdown(render_metric_card(t("total_matches", lang), "104", "72 Group + 32 Knockout"), unsafe_allow_html=True)
with m2:
    st.markdown(render_metric_card(t("finished", lang), finished), unsafe_allow_html=True)
with m3:
    st.markdown(render_metric_card(t("group_fixtures", lang), group_fixtures), unsafe_allow_html=True)
with m4:
    st.markdown(render_metric_card(t("groups", lang), groups), unsafe_allow_html=True)

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    t("fixtures_tab", lang),
    t("standings_tab", lang),
    t("bracket_tab", lang),
    t("top_players_tab", lang),
    t("live_api_tab", lang),
    t("squads_tab", lang),
    t("predictions_tab", lang),
])

# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(f"<div class='section-title'>{t('match_fixtures', lang)}</div>", unsafe_allow_html=True)

    groups_list = sorted(st.session_state.matches["Group"].unique())
    sel_group = st.selectbox(t("filter_by_group", lang), [t("all_groups", lang)] + [f"Group {g}" for g in groups_list], key="fixtures_group_filter")

    display_df = st.session_state.matches.copy()
    if sel_group != t("all_groups", lang):
        g_letter = sel_group.replace("Group ", "")
        display_df = display_df[display_df["Group"] == g_letter]
    display_df = sort_matches_by_kickoff(display_df)

    fixture_cards_html = []
    for _, row in display_df.iterrows():
        grp_color = GROUP_COLORS.get(str(row["Group"]), "#748CF7")
        match_time = format_match_datetime(row)
        status_html = (
            "<span class='status-live'>● LIVE</span>" if row["Status"] == "Live"
            else "<span class='status-finished'>✓ FT</span>" if row["Status"] == "Finished"
            else f"<span class='status-upcoming'>⏱ Soon · {match_time}</span>"
        )
        sa = row["Team A Score"] if row["Team A Score"] != "" else "—"
        sb = row["Team B Score"] if row["Team B Score"] != "" else "—"
        fixture_cards_html.append(f"""
        <div class='match-card'>
            <div style='display:flex;align-items:center;gap:8px;min-width:180px'>
                <span class='group-badge' style='background:{grp_color}22;color:{grp_color};border:1px solid {grp_color}44'>GRP {row["Group"]}</span>
                <span style='color:#5a6a8a;font-size:0.8rem'>{match_time}</span>
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
        </div>""")

    st.markdown("\n".join(fixture_cards_html), unsafe_allow_html=True)

    st.markdown(f"<div class='section-title'>{t('edit_scores', lang)}</div>", unsafe_allow_html=True)
    edited = st.data_editor(
        st.session_state.matches,
        num_rows="dynamic",
        width="stretch",
        hide_index=True,
        column_config={
            "Match ID": st.column_config.NumberColumn("ID", disabled=True),
            "Group": st.column_config.TextColumn("Grp"),
            "Date": st.column_config.TextColumn("Date"),
            "Time": st.column_config.TextColumn("Time"),
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
        if st.button(t("save_fixtures", lang), width="stretch"):
            st.session_state.matches = ensure_columns(edited.copy())
            st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)
            save_matches(st.session_state.matches)
            st.success(t("saved", lang))
    with c2:
        st.download_button(t("download_csv", lang), data=edited.to_csv(index=False).encode("utf-8"),
                           file_name="matches.csv", mime="text/csv", width="stretch")

# ════════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"<div class='section-title'>{t('group_standings', lang)}</div>", unsafe_allow_html=True)
    st.markdown(STANDINGS_LEGEND_HTML, unsafe_allow_html=True)
    if len(standings) == 0:
        st.info(t("enter_scores", lang))
    else:
        for grp in sorted(standings["Group"].unique()):
            grp_color = GROUP_COLORS.get(str(grp), "#748CF7")
            grp_df = standings[standings["Group"] == grp].copy()
            grp_df["Flag"] = grp_df["Team"].apply(flag)
            grp_df["Team"] = grp_df.apply(lambda r: f"{r['Flag']} {r['Team']}", axis=1)
            grp_df = grp_df[["Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]].reset_index(drop=True)
            grp_df.index = grp_df.index + 1

            st.markdown(f"<h3 style='color:{grp_color};font-family:Bebas Neue,sans-serif;letter-spacing:2px;text-align:center'>GROUP {grp}</h3>", unsafe_allow_html=True)
            st.markdown(render_centered_table(grp_df), unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f"<div class='section-title'>{t('tournament_bracket', lang)}</div>", unsafe_allow_html=True)
    qualifiers = get_qualifiers(standings)

    if len(qualifiers) < 4:
        st.info("🏆 Complete group stage matches to populate the bracket.")
        st.markdown("""
        **Full knockout structure:**
        - 🥊 Round of 32 — 32 teams
        - ⚔️ Round of 16 — 16 teams
        - 🏅 Quarterfinals — 8 teams
        - 🔥 Semifinals — 4 teams
        - 🏆 Final — 2 teams
        """)
    else:
        # ── ROUND OF 32 ───────────────────────────────────────────────────
        expected_r32 = build_round_of_32(qualifiers)
        saved_bracket = load_bracket()

        def render_round(df, title, key, interactive=True):
            st.markdown(f"<h3 style='color:#F7C948;font-family:Bebas Neue,sans-serif;letter-spacing:2px;margin-top:1.5rem'>{title}</h3>", unsafe_allow_html=True)
            if len(df) == 0:
                st.info("This stage will appear automatically once the earlier bracket rounds are available.")
                return df
            cols_count = min(4, len(df))
            cols = st.columns(cols_count)
            updated = df.copy()
            for i, (idx, row) in enumerate(df.iterrows()):
                with cols[i % cols_count]:
                    winner_class = "bracket-winner" if row["Winner"] else ""
                    st.markdown(f"""
                    <div class='bracket-match {winner_class}'>
                        <div>{flag(row["Team A"])} {row["Team A"]}</div>
                        <div style='color:#5a6a8a;font-size:0.75rem;text-align:center'>vs</div>
                        <div>{flag(row["Team B"])} {row["Team B"]}</div>
                        {"<div style='color:#F7C948;font-size:0.8rem;margin-top:4px'>🏆 " + row["Winner"] + "</div>" if row["Winner"] else ""}
                    </div>""", unsafe_allow_html=True)
                    options = ["—", row["Team A"], row["Team B"]]
                    current = row["Winner"] if row["Winner"] else "—"
                    if current not in options:
                        current = "—"
                    is_finished = str(row.get("Status", "")).strip() == "Finished"
                    if interactive and not is_finished:
                        choice = st.selectbox("Winner", options, index=options.index(current), key=f"{key}_{i}", label_visibility="collapsed")
                        updated.at[idx, "Winner"] = "" if choice == "—" else choice
                    elif interactive and is_finished:
                        st.caption("Final result")
            return updated

        def build_third_place_round(sf_round_df):
            losers = []
            for _, row in sf_round_df.iterrows():
                if not row["Winner"]:
                    continue
                loser = row["Team A"] if row["Winner"] == row["Team B"] else row["Team B"]
                losers.append(loser)
            if len(losers) != 2:
                return pd.DataFrame(columns=["Match", "Team A", "Team B", "Status", "Winner"])
            return pd.DataFrame([{
                "Match": "3rd Place",
                "Team A": losers[0],
                "Team B": losers[1],
                "Status": "Upcoming",
                "Winner": ""
            }])

        r32_live_matches = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES)
        r32 = restore_bracket_round(expected_r32, saved_bracket)
        r32 = apply_live_match_results(r32, r32_live_matches)
        r32 = render_round(r32, "🥊 ROUND OF 32", "r32", interactive=True)
        save_bracket_round(r32)

        # ── ROUND OF 16 ───────────────────────────────────────────────────
        r32_complete = r32["Winner"].ne("").all()
        if r32_complete:
            r16 = restore_bracket_round(advance_round(r32), saved_bracket)
            r16 = render_round(r16, "⚔️ ROUND OF 16", "r16", interactive=True)
            save_bracket_round(r16)
            r16_source = r16
        else:
            render_round(advance_round(r32), "⚔️ ROUND OF 16", "r16_preview", interactive=False)
            st.caption("Complete all Round of 32 winners to populate the Round of 16.")
            r16_source = advance_round(r32)

        # ── QUARTERFINALS ─────────────────────────────────────────────
        r16_complete = r32_complete and len(r16_source) > 0 and r16_source["Winner"].ne("").all()
        if r16_complete:
            qf = restore_bracket_round(advance_round(r16_source), saved_bracket)
            qf = render_round(qf, "🏅 QUARTERFINALS", "qf", interactive=True)
            save_bracket_round(qf)
            qf_source = qf
        else:
            render_round(advance_round(r16_source), "🏅 QUARTERFINALS", "qf_preview", interactive=False)
            st.caption("Complete all Round of 16 winners to populate the Quarterfinals.")
            qf_source = advance_round(r16_source)

        # ── SEMIFINALS ────────────────────────────────────────────
        qf_complete = r16_complete and len(qf_source) > 0 and qf_source["Winner"].ne("").all()
        if qf_complete:
            sf = restore_bracket_round(advance_round(qf_source), saved_bracket)
            sf = render_round(sf, "🔥 SEMIFINALS", "sf", interactive=True)
            save_bracket_round(sf)
            sf_source = sf
        else:
            render_round(advance_round(qf_source), "🔥 SEMIFINALS", "sf_preview", interactive=False)
            st.caption("Complete all Quarterfinal winners to populate the Semifinals.")
            sf_source = advance_round(qf_source)

        # ── FINAL ─────────────────────────────────────────────────
        sf_complete = qf_complete and len(sf_source) > 0 and sf_source["Winner"].ne("").all()
        if sf_complete:
            third_place = restore_bracket_round(build_third_place_round(sf_source), saved_bracket)
            if len(third_place) > 0:
                third_place = render_round(third_place, "🥉 3RD PLACE PLAYOFF", "third_place", interactive=True)
                save_bracket_round(third_place)
                third_winner = third_place["Winner"].iloc[0] if third_place["Winner"].iloc[0] else None
                if third_winner:
                    st.markdown(f"""
                    <div style='text-align:center;padding:1rem;background:linear-gradient(135deg,#1a1a00,#2a2a10);border:2px solid #CD7F32;border-radius:16px;margin-top:0.5rem'>
                        <div style='font-size:2.5rem'>{flag(third_winner)}</div>
                        <div style='font-family:Bebas Neue,sans-serif;font-size:2rem;color:#CD7F32;letter-spacing:3px'>{third_winner}</div>
                        <div style='color:#8a9ab5;font-size:0.9rem;margin-top:0.3rem'>🥉 3RD PLACE</div>
                    </div>""", unsafe_allow_html=True)

            final = restore_bracket_round(advance_round(sf_source), saved_bracket)
            final = render_round(final, "🏆 FINAL", "final", interactive=True)
            save_bracket_round(final)

            final_winner = final["Winner"].iloc[0] if len(final) and final["Winner"].iloc[0] else None
            if final_winner:
                st.balloons()
                st.markdown(f"""
                <div style='text-align:center;padding:2rem;background:linear-gradient(135deg,#1a2a00,#2a3a00);border:2px solid #F7C948;border-radius:16px;margin-top:1rem'>
                    <div style='font-size:4rem'>{flag(final_winner)}</div>
                    <div style='font-family:Bebas Neue,sans-serif;font-size:3rem;color:#F7C948;letter-spacing:3px'>{final_winner}</div>
                    <div style='color:#8a9ab5;font-size:1rem;margin-top:0.5rem'>🏆 FIFA WORLD CUP 2026 CHAMPION</div>
                </div>""", unsafe_allow_html=True)
        else:
            render_round(advance_round(sf_source), "🏆 FINAL", "final_preview", interactive=False)
            st.caption("Complete all Semifinal winners to populate the 3rd Place Playoff and Final.")

        if st.button("🔄 Reset Bracket", type="secondary"):
            clear_bracket()
            for key in list(st.session_state.keys()):
                if key.startswith(("r32_", "r16_", "qf_", "sf_", "third_place_", "final_")):
                    del st.session_state[key]
            st.rerun()

# ════════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown(f"<div class='section-title'>{t('top_performers', lang)}</div>", unsafe_allow_html=True)
    scorers = fetch_top_scorers()

    if scorers:
        st.markdown(t("top_scorers", lang))
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
    st.markdown(t("top_teams", lang))
    if len(standings) > 0:
        top_teams = standings.nlargest(10, "Pts")[["Group", "Team", "P", "W", "D", "L", "GF", "GA", "GD", "Pts"]].copy()
        top_teams["Flag"] = top_teams["Team"].apply(flag)
        top_teams["Team"] = top_teams.apply(lambda r: f"{r['Flag']} {r['Team']}", axis=1)
        top_teams = top_teams.drop("Flag", axis=1).reset_index(drop=True)
        top_teams.index = top_teams.index + 1
        st.markdown(render_centered_table(top_teams), unsafe_allow_html=True)
    else:
        st.info("Team performance stats will populate as matches are played.")

# ════════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown(f"<div class='section-title'>{t('live_api_data', lang)}</div>", unsafe_allow_html=True)

    if st.button(t("refresh_live", lang)):
        st.cache_data.clear()
        st.rerun()

    today_matches = todays_matches_for_display(
        fetch_todays_matches(),
        st.session_state.matches,
        normalize_team_name=normalize_team_name,
    )
    if today_matches:
        st.markdown(t("todays_matches", lang))
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
        st.markdown(t("live_standings", lang))
        st.markdown(STANDINGS_LEGEND_HTML, unsafe_allow_html=True)
        for s in api_standings:
            st.markdown(f"<h3 style='text-align:center'>{s.get('group', 'Group')}</h3>", unsafe_allow_html=True)
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
            st.markdown(render_centered_table(pd.DataFrame(rows), hide_index=True), unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown(f"<div class='section-title'>{t('key_players', lang)}</div>", unsafe_allow_html=True)

    # Search
    search = st.text_input(t("search_player", lang), placeholder=t("search_placeholder", lang))

    # Group filter
    all_groups = sorted(st.session_state.matches["Group"].unique())
    group_filter = st.selectbox(t("filter_by_group", lang), [t("all_groups", lang)] + [f"Group {g}" for g in all_groups], key="squads_group_filter")

    # Build team list filtered by group
    if group_filter != t("all_groups", lang):
        g_letter = group_filter.replace("Group ", "")
        group_teams = pd.unique(st.session_state.matches[st.session_state.matches["Group"] == g_letter][["Team A", "Team B"]].values.ravel("K"))
        group_teams = [t for t in group_teams if t and str(t).strip()]
    else:
        group_teams = list(KEY_PLAYERS.keys())

    for team in sorted(group_teams):
        players = KEY_PLAYERS.get(team, [])
        if not players:
            continue

        # Apply search filter
        if search:
            s = search.lower()
            players = [p for p in players if s in p[0].lower() or s in team.lower() or s in p[1].lower()]
            if not players:
                continue

        grp = st.session_state.matches[
            (st.session_state.matches["Team A"] == team) | (st.session_state.matches["Team B"] == team)
        ]["Group"]
        grp_letter = grp.iloc[0] if len(grp) else "?"
        grp_color = GROUP_COLORS.get(str(grp_letter), "#748CF7")

        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;margin:1.2rem 0 0.5rem 0'>
            <span style='font-size:1.8rem'>{flag(team)}</span>
            <h3 style='margin:0;font-family:Bebas Neue,sans-serif;letter-spacing:2px;color:#e8eaf0'>{team}</h3>
            <span class='group-badge' style='background:{grp_color}22;color:{grp_color};border:1px solid {grp_color}44'>GRP {grp_letter}</span>
        </div>""", unsafe_allow_html=True)

        cols = st.columns(len(players))
        for i, (name, pos, club) in enumerate(players):
            pos_color = {"Forward": "#FF6B6B", "Midfielder": "#F7C948", "Defender": "#48D8A0", "Goalkeeper": "#748CF7"}.get(pos, "#8a9ab5")
            with cols[i]:
                st.markdown(f"""
                <div class='player-card'>
                    <div style='font-size:1.6rem'>{flag(team)}</div>
                    <div style='font-weight:700;font-size:0.88rem;margin:6px 0 2px'>{name}</div>
                    <div style='display:inline-block;background:{pos_color}22;color:{pos_color};border:1px solid {pos_color}44;border-radius:10px;padding:1px 8px;font-size:0.72rem;margin-bottom:4px'>{pos}</div>
                    <div style='color:#5a6a8a;font-size:0.72rem'>{club}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#1a2235;margin:0.5rem 0'>", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
with tab7:
    st.markdown(f"<div class='section-title'>{t('prediction_game', lang)}</div>", unsafe_allow_html=True)

    # ── PLAYER NAME ───────────────────────────────────────────────────────────
    st.markdown(t("who_are_you", lang))
    name_input = st.text_input(t("enter_name", lang), value=st.session_state.player_name,
                                placeholder="e.g. Ralph, Miru, Duke...", key="name_input")
    if name_input:
        st.session_state.player_name = name_input.strip()

    if not st.session_state.player_name:
        st.info(t("enter_name_info", lang))
    else:
        player = st.session_state.player_name
        st.markdown(f"<p style='color:#48D8A0;font-weight:700'>{t('playing_as', lang)}: {player} 🎮</p>", unsafe_allow_html=True)
        prediction_result_source = build_prediction_result_source(st.session_state.matches)
        prediction_match_catalog = build_prediction_match_catalog(prediction_result_source)
        visible_prediction_match_catalog = prediction_match_catalog[prediction_match_catalog["Group"] == "QF"].copy()
        prediction_match_labels = build_prediction_match_labels(visible_prediction_match_catalog)
        prediction_match_ids = visible_prediction_match_catalog["Match ID"].tolist()

        # Score existing predictions
        st.session_state.predictions = refresh_prediction_scores(st.session_state.predictions, prediction_match_catalog)

        st.markdown(t("pick_winners", lang))

        def render_knockout_prediction_cards(round_group, round_title):
            round_matches = visible_prediction_match_catalog[visible_prediction_match_catalog["Group"] == round_group].copy()

            if len(round_matches) == 0:
                st.info("No matches available yet.")
                return

            for _, match in round_matches.iterrows():
                match_id = match["Match ID"]
                finished = match["Status"] == "Finished"
                locked = is_match_locked(match)
                existing = st.session_state.predictions[
                    (st.session_state.predictions["Player"] == player) &
                    (st.session_state.predictions["Match ID"] == match_id)
                ]
                already_picked = existing.iloc[0]["Predicted Winner"] if len(existing) > 0 else None
                pick_result = existing.iloc[0]["Correct"] if len(existing) > 0 else ""
                status_badge = "🏁 Final" if finished else ("🔒 Locked" if locked else "🟢 Open")
                status_color = "#F7C948" if finished else ("#FF6B6B" if locked else "#48D8A0")
                badge_color = "#F7C948" if round_group == "R32" else "#5BA7FF"
                result_badge = ""
                if finished and already_picked and pick_result in ("✅", "❌"):
                    result_color = "#48D8A0" if pick_result == "✅" else "#FF6B6B"
                    result_text = "Won" if pick_result == "✅" else "Lost"
                    result_badge = f"<span style='color:{result_color};font-size:0.8rem'>{pick_result} {result_text}</span>"

                st.markdown(f"""
                <div class='match-card' style='margin-bottom:0.3rem'>
                    <span class='group-badge' style='background:{badge_color}22;color:{badge_color};border:1px solid {badge_color}44'>{round_group}</span>
                    <span style='color:#5a6a8a;font-size:0.8rem'>{round_title}</span>
                    <span style='font-weight:700'>{flag(match["Team A"])} {match["Team A"]} vs {match["Team B"]} {flag(match["Team B"])}</span>
                    <span style='color:{status_color};font-size:0.75rem'>{status_badge}</span>
                    {"<span style='color:#F7C948;font-size:0.8rem'>" + t("your_pick", lang) + ": " + already_picked + "</span>" if already_picked else ""}
                    {result_badge}
                </div>""", unsafe_allow_html=True)

                if not finished and not locked:
                    pick_placeholder = t("pick_winner_placeholder", lang)
                    knockout_options = [pick_placeholder, match["Team A"], match["Team B"], "Draw"]
                    current_idx = 0
                    if already_picked and already_picked in knockout_options:
                        current_idx = knockout_options.index(already_picked)

                    pick_label = f"Pick winner for {match['Team A']} vs {match['Team B']}"
                    pick = st.selectbox(
                        pick_label,
                        knockout_options,
                        index=current_idx,
                        key=(
                            f"{round_group.lower()}_v2_pred_{player}_{match_id}"
                            if round_group in ("R16", "QF")
                            else f"{round_group.lower()}_pred_{player}_{match_id}"
                        ),
                        label_visibility="collapsed",
                    )

                    if pick != pick_placeholder and pick != already_picked:
                        correct = prediction_result_for_pick(prediction_match_catalog, match_id, pick)
                        save_prediction(player, match_id, pick, correct=correct)
                        st.session_state.predictions = st.session_state.predictions[
                            ~((st.session_state.predictions["Player"] == player) &
                              (st.session_state.predictions["Match ID"] == match_id))
                        ]
                        new_row = pd.DataFrame([{
                            "Player": player,
                            "Match ID": match_id,
                            "Predicted Winner": pick,
                            "Correct": correct
                        }])
                        st.session_state.predictions = pd.concat(
                            [st.session_state.predictions, new_row], ignore_index=True
                        )

        st.markdown("### Quarterfinal Predictions")
        render_knockout_prediction_cards("QF", "Quarterfinal Predictions")

        # ── MY PREDICTIONS ────────────────────────────────────────────────────
        st.markdown(t("my_predictions", lang))
        my_preds = st.session_state.predictions[
            (st.session_state.predictions["Player"] == player) &
            (st.session_state.predictions["Match ID"].isin(prediction_match_ids))
        ].copy()
        if len(my_preds) == 0:
            st.info(t("no_my_predictions", lang))
        else:
            my_preds = my_preds.merge(
                prediction_match_labels[["Match ID", "Team A", "Team B", "Kickoff", "Group", "Match"]],
                on="Match ID", how="left"
            )
            display_preds = my_preds[["Kickoff", "Group", "Match", "Predicted Winner", "Correct"]].rename(
                columns={"Predicted Winner": "Your Pick", "Correct": "Result"}
            )
            st.markdown(render_centered_table(display_preds, hide_index=True), unsafe_allow_html=True)

    # Refresh persisted predictions before shared views so other players appear.
    st.session_state.predictions = load_predictions()
    prediction_result_source = build_prediction_result_source(st.session_state.matches)
    prediction_match_catalog = build_prediction_match_catalog(prediction_result_source)
    visible_prediction_match_catalog = prediction_match_catalog[prediction_match_catalog["Group"] == "QF"].copy()
    prediction_match_labels = build_prediction_match_labels(visible_prediction_match_catalog)
    prediction_match_ids = visible_prediction_match_catalog["Match ID"].tolist()
    st.session_state.predictions = refresh_prediction_scores(st.session_state.predictions, prediction_match_catalog)
    active_predictions = filter_predictions_to_catalog(st.session_state.predictions, visible_prediction_match_catalog)

    # ── LEADERBOARD ───────────────────────────────────────────────────────
    st.markdown(t("leaderboard", lang))
    lb = get_leaderboard(active_predictions)
    if len(lb) == 0:
        st.info(t("leaderboard_empty", lang))
    else:
        medals = ["🥇", "🥈", "🥉"]
        for i, row in lb.iterrows():
            medal = medals[i] if i < 3 else f"{i+1}."
            bar_width = int((row["Points"] / (lb["Points"].max() + 1)) * 100)
            st.markdown(f"""
            <div class='match-card' style='margin:4px 0'>
                <span style='font-size:1.3rem'>{medal}</span>
                <span style='font-weight:700;min-width:120px'>{row["Player"]}</span>
                <div style='flex:1;background:#0a0e1a;border-radius:6px;height:12px;margin:0 12px'>
                    <div style='width:{bar_width}%;background:linear-gradient(90deg,#F7C948,#FF9F43);height:100%;border-radius:6px'></div>
                </div>
                <span style='color:#F7C948;font-family:Bebas Neue,sans-serif;font-size:1.2rem'>{row["Points"]} pts</span>
                <span style='color:#48D8A0;font-size:0.8rem'>{row["Correct"]}/{row["Predicted"]} correct ({row["Accuracy"]})</span>
            </div>""", unsafe_allow_html=True)

    # ── ALL PLAYERS PREDICTIONS GRID ──────────────────────────────────────
    st.markdown(t("everyone_picks", lang))
    all_preds = active_predictions.copy()
    if len(all_preds) == 0:
        st.info(t("no_predictions", lang))
    else:
        all_players = sorted(all_preds["Player"].unique())
        # Build match labels
        match_labels = build_prediction_match_labels(visible_prediction_match_catalog)
        # Pivot: rows=matches, cols=players
        grid = match_labels[["Match ID", "Date", "Kickoff", "Group", "Match"]].copy()
        for p in all_players:
            p_preds = all_preds[all_preds["Player"] == p][["Match ID", "Predicted Winner", "Correct"]].copy()
            p_preds.columns = ["Match ID", p, f"{p}_result"]
            grid = grid.merge(p_preds, on="Match ID", how="left")
            # Combine pick + result into one cell
            def fmt(row, p=p):
                pick = row[p] if pd.notna(row[p]) else "—"
                result = row[f"{p}_result"] if pd.notna(row.get(f"{p}_result")) else ""
                return f"{pick} {result}".strip()
            grid[p] = grid.apply(fmt, axis=1)
            grid = grid.drop(columns=[f"{p}_result"])

        display_grid = grid[["Kickoff", "Group", "Match"] + all_players]
        st.markdown(render_centered_table(display_grid, hide_index=True), unsafe_allow_html=True)
