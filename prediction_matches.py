import pandas as pd


ROUND_OF_32_PREDICTION_MATCHES = [
    {"Match ID": 1001, "Group": "R32", "Date": "", "Time": "", "Team A": "South Africa", "Team B": "Canada", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1002, "Group": "R32", "Date": "", "Time": "", "Team A": "Brazil", "Team B": "Japan", "Status": "Finished", "Winner": "Brazil"},
    {"Match ID": 1003, "Group": "R32", "Date": "", "Time": "", "Team A": "Germany", "Team B": "Paraguay", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1004, "Group": "R32", "Date": "", "Time": "", "Team A": "Netherlands", "Team B": "Morocco", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1005, "Group": "R32", "Date": "", "Time": "", "Team A": "Ivory Coast", "Team B": "Norway", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1006, "Group": "R32", "Date": "", "Time": "", "Team A": "France", "Team B": "Sweden", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1007, "Group": "R32", "Date": "", "Time": "", "Team A": "Mexico", "Team B": "Ecuador", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1008, "Group": "R32", "Date": "", "Time": "", "Team A": "England", "Team B": "DR Congo", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1009, "Group": "R32", "Date": "", "Time": "", "Team A": "Belgium", "Team B": "Senegal", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1010, "Group": "R32", "Date": "", "Time": "", "Team A": "United States", "Team B": "Bosnia and Herzegovina", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1011, "Group": "R32", "Date": "", "Time": "", "Team A": "Switzerland", "Team B": "Algeria", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1012, "Group": "R32", "Date": "", "Time": "", "Team A": "Spain", "Team B": "Austria", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1013, "Group": "R32", "Date": "", "Time": "", "Team A": "Argentina", "Team B": "Cape Verde", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1014, "Group": "R32", "Date": "", "Time": "", "Team A": "Colombia", "Team B": "Ghana", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1015, "Group": "R32", "Date": "", "Time": "", "Team A": "Portugal", "Team B": "Croatia", "Status": "Upcoming", "Winner": ""},
    {"Match ID": 1016, "Group": "R32", "Date": "", "Time": "", "Team A": "Australia", "Team B": "Egypt", "Status": "Upcoming", "Winner": ""},
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
