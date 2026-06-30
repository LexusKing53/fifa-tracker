import pandas as pd


ROUND_OF_32_PREDICTION_MATCHES = [
    {"Match ID": 1001, "Group": "R32", "Date": "2026-06-28", "Time": "", "Team A": "South Africa", "Team B": "Canada", "Status": "Finished", "Winner": "Canada"},
    {"Match ID": 1002, "Group": "R32", "Date": "2026-06-29", "Time": "", "Team A": "Brazil", "Team B": "Japan", "Status": "Finished", "Winner": "Brazil"},
    {"Match ID": 1003, "Group": "R32", "Date": "2026-06-29", "Time": "", "Team A": "Germany", "Team B": "Paraguay", "Status": "Finished", "Winner": "Paraguay"},
    {"Match ID": 1004, "Group": "R32", "Date": "2026-06-29", "Time": "", "Team A": "Netherlands", "Team B": "Morocco", "Status": "Finished", "Winner": "Morocco"},
    {"Match ID": 1005, "Group": "R32", "Date": "2026-06-30", "Time": "1:00 PM ET", "Team A": "Ivory Coast", "Team B": "Norway", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1006, "Group": "R32", "Date": "2026-06-30", "Time": "5:00 PM ET", "Team A": "France", "Team B": "Sweden", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1007, "Group": "R32", "Date": "2026-06-30", "Time": "9:00 PM ET", "Team A": "Mexico", "Team B": "Ecuador", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1008, "Group": "R32", "Date": "2026-07-01", "Time": "12:00 PM ET", "Team A": "England", "Team B": "DR Congo", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1009, "Group": "R32", "Date": "2026-07-01", "Time": "4:00 PM ET", "Team A": "Belgium", "Team B": "Senegal", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1010, "Group": "R32", "Date": "2026-07-01", "Time": "8:00 PM ET", "Team A": "United States", "Team B": "Bosnia and Herzegovina", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1011, "Group": "R32", "Date": "2026-07-02", "Time": "11:00 PM ET", "Team A": "Switzerland", "Team B": "Algeria", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1012, "Group": "R32", "Date": "2026-07-02", "Time": "2:00 PM ET", "Team A": "Spain", "Team B": "Austria", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1013, "Group": "R32", "Date": "2026-07-03", "Time": "5:00 PM ET", "Team A": "Argentina", "Team B": "Cape Verde", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1014, "Group": "R32", "Date": "2026-07-03", "Time": "8:00 PM ET", "Team A": "Colombia", "Team B": "Ghana", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1015, "Group": "R32", "Date": "2026-07-02", "Time": "5:00 PM ET", "Team A": "Portugal", "Team B": "Croatia", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1016, "Group": "R32", "Date": "2026-07-03", "Time": "2:00 PM ET", "Team A": "Australia", "Team B": "Egypt", "Status": "Upcoming", "Winner": ""},
]


def build_prediction_match_catalog(group_matches_df):
    base_cols = ["Match ID", "Group", "Date", "Time", "Team A", "Team B", "Status", "Winner"]
    match_catalog = group_matches_df.copy()
    for column in base_cols:
        if column not in match_catalog.columns:
            match_catalog[column] = ""
    match_catalog = match_catalog[base_cols]
    match_catalog = match_catalog[match_catalog["Status"] != "Finished"].copy()

    r32_matches = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES)
    return pd.concat([match_catalog, r32_matches], ignore_index=True)
