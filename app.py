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
    "Denmark":     [("Christian Eriksen","Midfielder","Man United"),("Pierre-Emile Højbjerg","Midfielder","Marseille"),("Rasmus Højlund","Forward","Man United"),("Kasper Schmeichel","Goalkeeper","Anderlecht"),("Joakim Mæhle","Defender","Atalanta")],
    "Poland":      [("Robert Lewandowski","Forward","Barcelona"),("Piotr Zieliński","Midfielder","Inter Milan"),("Wojciech Szczęsny","Goalkeeper","Barcelona"),("Jakub Kiwior","Defender","Arsenal"),("Nicola Zalewski","Midfielder","Roma")],
    "Serbia":      [("Aleksandar Mitrović","Forward","Al Hilal"),("Dušan Vlahović","Forward","Juventus"),("Nemanja Gudelj","Midfielder","Sevilla"),("Vanja Milinković-Savić","Goalkeeper","Torino"),("Dušan Tadić","Midfielder","Fenerbahçe")],
    "Iran":        [("Sardar Azmoun","Forward","Bayer Leverkusen"),("Alireza Jahanbakhsh","Forward","Feyenoord"),("Mehdi Taremi","Forward","Inter Milan"),("Ali Beiranvand","Goalkeeper","Persepolis"),("Saman Ghoddos","Midfielder","Brentford")],
    "Saudi Arabia":[("Salem Al-Dawsari","Forward","Al Hilal"),("Mohammed Al-Owais","Goalkeeper","Al Hilal"),("Saud Abdulhamid","Defender","Roma"),("Firas Al-Buraikan","Forward","Al Fateh"),("Saleh Al-Shehri","Forward","Al Hilal")],
    "Ghana":       [("Jordan Ayew","Forward","Crystal Palace"),("Thomas Partey","Midfielder","Arsenal"),("André Ayew","Forward","Le Havre"),("Mohammed Kudus","Forward","West Ham"),("Lawrence Ati-Zigi","Goalkeeper","St. Gallen")],
    "Ivory Coast": [("Sébastien Haller","Forward","Dortmund"),("Franck Kessié","Midfielder","Barcelona"),("Serge Aurier","Defender","Villarreal"),("Wilfried Zaha","Forward","Galatasaray"),("Maxwel Cornet","Forward","Southampton")],
    "Egypt":       [("Mohamed Salah","Forward","Liverpool"),("Mohamed El Shenawy","Goalkeeper","Al Ahly"),("Ahmed Hegazy","Defender","Al Ittihad"),("Trezeguet","Forward","Istanbul Başakşehir"),("Amr El Sulaya","Midfielder","Al Ahly")],
    "Nigeria":     [("Victor Osimhen","Forward","Napoli"),("Wilfred Ndidi","Midfielder","Leicester"),("Alex Iwobi","Midfielder","Fulham"),("Stanley Nwabali","Goalkeeper","Chippa United"),("Semi Ajayi","Defender","West Brom")],
    "Scotland":    [("Andrew Robertson","Defender","Liverpool"),("Scott McTominay","Midfielder","Napoli"),("Kieran Tierney","Defender","Real Sociedad"),("Angus Gunn","Goalkeeper","Norwich"),("John McGinn","Midfielder","Aston Villa")],
    "Turkey":      [("Hakan Çalhanoğlu","Midfielder","Inter Milan"),("Arda Güler","Midfielder","Real Madrid"),("Kenan Yıldız","Forward","Juventus"),("Çağlar Söyüncü","Defender","Atlético Madrid"),("Mert Günok","Goalkeeper","Beşiktaş")],
    "Austria":     [("David Alaba","Defender","Real Madrid"),("Marcel Sabitzer","Midfielder","Dortmund"),("Marko Arnautović","Forward","Man United"),("Konrad Laimer","Midfielder","Bayern Munich"),("Patrick Pentz","Goalkeeper","Bayer Leverkusen")],
    "Ukraine":     [("Oleksandr Zinchenko","Defender","Arsenal"),("Mykhailo Mudryk","Forward","Chelsea"),("Viktor Tsygankov","Forward","Girona"),("Georgiy Sudakov","Midfielder","Shakhtar"),("Andriy Lunin","Goalkeeper","Real Madrid")],
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
    "Scotland":    [("Andrew Robertson","Defender","Liverpool"),("Scott McTominay","Midfielder","Napoli"),("Kieran Tierney","Defender","Real Sociedad"),("Angus Gunn","Goalkeeper","Norwich"),("John McGinn","Midfielder","Aston Villa")],
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
    {"Match ID": 32, "Group": "F", "Date": "2026-06-14", "Team A": "Ukraine",      "Team B": "Tunisia",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Monterrey"},
    {"Match ID": 33, "Group": "F", "Date": "2026-06-20", "Team A": "Netherlands",  "Team B": "Ukraine",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Houston Stadium"},
    {"Match ID": 34, "Group": "F", "Date": "2026-06-20", "Team A": "Tunisia",      "Team B": "Japan",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Estadio Monterrey"},
    {"Match ID": 35, "Group": "F", "Date": "2026-06-25", "Team A": "Japan",        "Team B": "Ukraine",      "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Dallas Stadium"},
    {"Match ID": 36, "Group": "F", "Date": "2026-06-25", "Team A": "Tunisia",      "Team B": "Netherlands",  "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "Kansas City Stadium"},
    # ── GROUP G ──────────────────────────────────────────────────────────────
    {"Match ID": 37, "Group": "G", "Date": "2026-06-15", "Team A": "Belgium",      "Team B": "Egypt",        "Team A Score": "", "Team B Score": "", "Winner": "", "Loser": "", "Status": "Upcoming", "Venue": "BC Place"},
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

def advance_round(prev_round_df):
    """Takes winners from a round and pairs them into the next round."""
    winners = list(prev_round_df["Winner"].values)
    pairs = []
    label_map = {"R32": "R16", "R16": "QF", "QF": "SF", "SF": "F"}
    prefix = prev_round_df["Match"].iloc[0].split("-")[0] if len(prev_round_df) else "R32"
    next_prefix = label_map.get(prefix, "Next")
    for i in range(0, len(winners), 2):
        if i + 1 < len(winners):
            ta = winners[i] if winners[i] else f"Winner M{i+1}"
            tb = winners[i+1] if winners[i+1] else f"Winner M{i+2}"
            pairs.append({"Match": f"{next_prefix}-{i//2+1}", "Team A": ta, "Team B": tb, "Status": "Upcoming", "Winner": ""})
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

# ── PREDICTIONS ───────────────────────────────────────────────────────────────
PREDICTIONS_FILE = Path("predictions.csv")

def load_predictions():
    if PREDICTIONS_FILE.exists():
        return pd.read_csv(PREDICTIONS_FILE)
    return pd.DataFrame(columns=["Player", "Match ID", "Predicted Winner", "Correct"])

def save_predictions(df):
    df.to_csv(PREDICTIONS_FILE, index=False)

def is_match_locked(match_row):
    try:
        match_date = pd.to_datetime(match_row["Date"])
        return match_date.date() <= datetime.now().date()
    except Exception:
        return False

def score_predictions(predictions, matches):
    updated = predictions.copy()
    for idx, row in updated.iterrows():
        match = matches[matches["Match ID"] == row["Match ID"]]
        if len(match) == 0:
            continue
        match = match.iloc[0]
        if match["Status"] != "Finished":
            updated.at[idx, "Correct"] = ""
            continue
        updated.at[idx, "Correct"] = "✅" if row["Predicted Winner"] == match["Winner"] else "❌"
    return updated

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

if st_autorefresh:
    st_autorefresh(interval=60000, key="refresh")

st.session_state.matches = ensure_columns(st.session_state.matches)
st.session_state.matches = st.session_state.matches.apply(compute_match_outcome, axis=1)
standings = build_standings(st.session_state.matches)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@keyframes spin { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
.spin-ball { display:inline-block; animation:spin 2s linear infinite; font-size:3.5rem; line-height:1; }
</style>
<div style='display:flex;align-items:center;gap:1rem;padding:0.5rem 0'>
    <span class='spin-ball'>⚽</span>
    <div>
        <h1 style='font-size:3.5rem;margin:0;color:#F7C948;font-family:Bebas Neue,sans-serif;letter-spacing:3px'>FIFA WORLD CUP 2026</h1>
        <p style='color:#5a6a8a;margin:0;font-size:0.85rem'>🔄 Updated """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
    </div>
    <span class='spin-ball'>⚽</span>
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
upcoming = int((st.session_state.matches["Status"] == "Upcoming").sum())
groups = st.session_state.matches["Group"].nunique()
m1.metric("⚽ Total Matches", total)
m2.metric("✅ Finished", finished)
m3.metric("🕐 Upcoming", upcoming)
m4.metric("🏟️ Groups", groups)

st.markdown("---")

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["📅 FIXTURES", "📊 STANDINGS", "🏆 BRACKET", "⭐ TOP PLAYERS", "📡 LIVE API", "👟 SQUADS", "🎯 PREDICTIONS"])

# ════════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div class='section-title'>MATCH FIXTURES</div>", unsafe_allow_html=True)

    groups_list = sorted(st.session_state.matches["Group"].unique())
    sel_group = st.selectbox("Filter by Group", ["All Groups"] + [f"Group {g}" for g in groups_list], key="fixtures_group_filter")

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
        if "r32" not in st.session_state:
            st.session_state.r32 = build_round_of_32(qualifiers)

        def render_round(df, title, key):
            st.markdown(f"<h3 style='color:#F7C948;font-family:Bebas Neue,sans-serif;letter-spacing:2px;margin-top:1.5rem'>{title}</h3>", unsafe_allow_html=True)
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
                    choice = st.selectbox("Winner", options, index=options.index(current), key=f"{key}_{i}", label_visibility="collapsed")
                    updated.at[idx, "Winner"] = "" if choice == "—" else choice
            return updated

        st.session_state.r32 = render_round(st.session_state.r32, "🥊 ROUND OF 32", "r32")

        # ── ROUND OF 16 ───────────────────────────────────────────────────
        r32_complete = st.session_state.r32["Winner"].ne("").all()
        if r32_complete:
            if "r16" not in st.session_state or len(st.session_state.r16) == 0:
                st.session_state.r16 = advance_round(st.session_state.r32)
            st.session_state.r16 = render_round(st.session_state.r16, "⚔️ ROUND OF 16", "r16")

            # ── QUARTERFINALS ─────────────────────────────────────────────
            r16_complete = st.session_state.r16["Winner"].ne("").all()
            if r16_complete:
                if "qf" not in st.session_state or len(st.session_state.qf) == 0:
                    st.session_state.qf = advance_round(st.session_state.r16)
                st.session_state.qf = render_round(st.session_state.qf, "🏅 QUARTERFINALS", "qf")

                # ── SEMIFINALS ────────────────────────────────────────────
                qf_complete = st.session_state.qf["Winner"].ne("").all()
                if qf_complete:
                    if "sf" not in st.session_state or len(st.session_state.sf) == 0:
                        st.session_state.sf = advance_round(st.session_state.qf)
                    st.session_state.sf = render_round(st.session_state.sf, "🔥 SEMIFINALS", "sf")

                    # ── FINAL ─────────────────────────────────────────────
                    sf_complete = st.session_state.sf["Winner"].ne("").all()
                    if sf_complete:
                        if "final" not in st.session_state or len(st.session_state.final) == 0:
                            st.session_state.final = advance_round(st.session_state.sf)
                        st.session_state.final = render_round(st.session_state.final, "🏆 FINAL", "final")

                        final_winner = st.session_state.final["Winner"].iloc[0] if len(st.session_state.final) and st.session_state.final["Winner"].iloc[0] else None
                        if final_winner:
                            st.balloons()
                            st.markdown(f"""
                            <div style='text-align:center;padding:2rem;background:linear-gradient(135deg,#1a2a00,#2a3a00);border:2px solid #F7C948;border-radius:16px;margin-top:1rem'>
                                <div style='font-size:4rem'>{flag(final_winner)}</div>
                                <div style='font-family:Bebas Neue,sans-serif;font-size:3rem;color:#F7C948;letter-spacing:3px'>{final_winner}</div>
                                <div style='color:#8a9ab5;font-size:1rem;margin-top:0.5rem'>🏆 FIFA WORLD CUP 2026 CHAMPION</div>
                            </div>""", unsafe_allow_html=True)

        if st.button("🔄 Reset Bracket", type="secondary"):
            for key in ["r32", "r16", "qf", "sf", "final"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

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

# ════════════════════════════════════════════════════════════════════════════════
with tab6:
    st.markdown("<div class='section-title'>KEY PLAYERS BY TEAM</div>", unsafe_allow_html=True)

    # Search
    search = st.text_input("🔍 Search player or team", placeholder="e.g. Messi, Brazil, Forward...")

    # Group filter
    all_groups = sorted(st.session_state.matches["Group"].unique())
    group_filter = st.selectbox("Filter by Group", ["All Groups"] + [f"Group {g}" for g in all_groups], key="squads_group_filter")

    # Build team list filtered by group
    if group_filter != "All Groups":
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
    st.markdown("<div class='section-title'>PREDICTION GAME</div>", unsafe_allow_html=True)

    # ── PLAYER NAME ───────────────────────────────────────────────────────────
    st.markdown("### 👤 Who are you?")
    name_input = st.text_input("Enter your name to play", value=st.session_state.player_name,
                                placeholder="e.g. Ralph, Miru, Duke...", key="name_input")
    if name_input:
        st.session_state.player_name = name_input.strip()

    if not st.session_state.player_name:
        st.info("Enter your name above to start making predictions.")
    else:
        player = st.session_state.player_name
        st.markdown(f"<p style='color:#48D8A0;font-weight:700'>Playing as: {player} 🎮</p>", unsafe_allow_html=True)

        # Score existing predictions
        st.session_state.predictions = score_predictions(st.session_state.predictions, st.session_state.matches)

        # ── UPCOMING MATCHES TO PREDICT ───────────────────────────────────────
        st.markdown("### ⚽ Pick Your Winners")
        upcoming = st.session_state.matches[st.session_state.matches["Status"] != "Finished"].copy()

        if len(upcoming) == 0:
            st.success("All matches have finished!")
        else:
            made_any = False
            for _, match in upcoming.iterrows():
                match_id = match["Match ID"]
                locked = is_match_locked(match)

                # Check if this player already predicted this match
                existing = st.session_state.predictions[
                    (st.session_state.predictions["Player"] == player) &
                    (st.session_state.predictions["Match ID"] == match_id)
                ]
                already_picked = existing.iloc[0]["Predicted Winner"] if len(existing) > 0 else None

                grp_color = GROUP_COLORS.get(str(match["Group"]), "#748CF7")
                lock_badge = "<span style='color:#FF6B6B;font-size:0.75rem'>🔒 Locked</span>" if locked else "<span style='color:#48D8A0;font-size:0.75rem'>🟢 Open</span>"

                st.markdown(f"""
                <div class='match-card' style='margin-bottom:0.3rem'>
                    <span class='group-badge' style='background:{grp_color}22;color:{grp_color};border:1px solid {grp_color}44'>GRP {match["Group"]}</span>
                    <span style='color:#5a6a8a;font-size:0.8rem'>{match["Date"]}</span>
                    <span style='font-weight:700'>{flag(match["Team A"])} {match["Team A"]} vs {match["Team B"]} {flag(match["Team B"])}</span>
                    {lock_badge}
                    {"<span style='color:#F7C948;font-size:0.8rem'>Your pick: " + already_picked + "</span>" if already_picked else ""}
                </div>""", unsafe_allow_html=True)

                if not locked:
                    options = ["— Pick a winner —", match["Team A"], match["Team B"], "Draw"]
                    current_idx = 0
                    if already_picked and already_picked in options:
                        current_idx = options.index(already_picked)

                    pick = st.selectbox("", options, index=current_idx,
                                       key=f"pred_{player}_{match_id}",
                                       label_visibility="collapsed")

                    if pick != "— Pick a winner —" and pick != already_picked:
                        # Save prediction
                        new_row = pd.DataFrame([{
                            "Player": player,
                            "Match ID": match_id,
                            "Predicted Winner": pick,
                            "Correct": ""
                        }])
                        # Remove old prediction for this match if exists
                        st.session_state.predictions = st.session_state.predictions[
                            ~((st.session_state.predictions["Player"] == player) &
                              (st.session_state.predictions["Match ID"] == match_id))
                        ]
                        st.session_state.predictions = pd.concat(
                            [st.session_state.predictions, new_row], ignore_index=True
                        )
                        save_predictions(st.session_state.predictions)
                        made_any = True

        # ── LEADERBOARD ───────────────────────────────────────────────────────
        st.markdown("### 🏆 Leaderboard")
        lb = get_leaderboard(st.session_state.predictions)
        if len(lb) == 0:
            st.info("Leaderboard populates once matches finish.")
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

        # ── MY PREDICTIONS ────────────────────────────────────────────────────
        st.markdown("### 📋 My Predictions")
        my_preds = st.session_state.predictions[st.session_state.predictions["Player"] == player].copy()
        if len(my_preds) == 0:
            st.info("You haven't made any predictions yet.")
        else:
            my_preds = my_preds.merge(
                st.session_state.matches[["Match ID", "Team A", "Team B", "Date", "Group"]],
                on="Match ID", how="left"
            )
            my_preds["Match"] = my_preds.apply(
                lambda r: f"{flag(r['Team A'])} {r['Team A']} vs {r['Team B']} {flag(r['Team B'])}", axis=1
            )
            display_preds = my_preds[["Date", "Group", "Match", "Predicted Winner", "Correct"]].rename(
                columns={"Predicted Winner": "Your Pick", "Correct": "Result"}
            )
            st.dataframe(display_preds, use_container_width=True, hide_index=True)
