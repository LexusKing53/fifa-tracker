import pandas as pd


ROUND_OF_32_PREDICTION_MATCHES = [
    {"Match ID": 1001, "Group": "R32", "Date": "2026-06-28", "Time": "", "Team A": "South Africa", "Team B": "Canada", "Status": "Finished", "Winner": "Canada"},
    {"Match ID": 1002, "Group": "R32", "Date": "2026-06-29", "Time": "", "Team A": "Brazil", "Team B": "Japan", "Status": "Finished", "Winner": "Brazil"},
    {"Match ID": 1003, "Group": "R32", "Date": "2026-06-29", "Time": "", "Team A": "Germany", "Team B": "Paraguay", "Status": "Finished", "Winner": "Paraguay"},
    {"Match ID": 1004, "Group": "R32", "Date": "2026-06-29", "Time": "", "Team A": "Netherlands", "Team B": "Morocco", "Status": "Finished", "Winner": "Morocco"},
    {"Match ID": 1005, "Group": "R32", "Date": "2026-06-30", "Time": "1:00 PM ET", "Team A": "Ivory Coast", "Team B": "Norway", "Status": "Finished", "Winner": "Norway"},
    {"Match ID": 1006, "Group": "R32", "Date": "2026-06-30", "Time": "5:00 PM ET", "Team A": "France", "Team B": "Sweden", "Status": "Finished", "Winner": "France"},
    {"Match ID": 1007, "Group": "R32", "Date": "2026-06-30", "Time": "9:00 PM ET", "Team A": "Mexico", "Team B": "Ecuador", "Status": "Finished", "Winner": "Mexico"},
    {"Match ID": 1008, "Group": "R32", "Date": "2026-07-01", "Time": "12:00 PM ET", "Team A": "England", "Team B": "DR Congo", "Status": "Finished", "Winner": "England"},
    {"Match ID": 1009, "Group": "R32", "Date": "2026-07-01", "Time": "4:00 PM ET", "Team A": "Belgium", "Team B": "Senegal", "Status": "Finished", "Winner": "Belgium"},
    {"Match ID": 1010, "Group": "R32", "Date": "2026-07-01", "Time": "8:00 PM ET", "Team A": "United States", "Team B": "Bosnia and Herzegovina", "Status": "Finished", "Winner": "United States"},
    {"Match ID": 1011, "Group": "R32", "Date": "2026-07-02", "Time": "11:00 PM ET", "Team A": "Switzerland", "Team B": "Algeria", "Status": "Finished", "Winner": "Switzerland"},
    {"Match ID": 1012, "Group": "R32", "Date": "2026-07-02", "Time": "2:00 PM ET", "Team A": "Spain", "Team B": "Austria", "Status": "Finished", "Winner": "Spain"},
    {"Match ID": 1013, "Group": "R32", "Date": "2026-07-03", "Time": "5:00 PM ET", "Team A": "Argentina", "Team B": "Cape Verde", "Status": "Finished", "Winner": "Argentina"},
    {"Match ID": 1014, "Group": "R32", "Date": "2026-07-03", "Time": "8:00 PM ET", "Team A": "Colombia", "Team B": "Ghana", "Status": "Finished", "Winner": "Colombia"},
    {"Match ID": 1015, "Group": "R32", "Date": "2026-07-02", "Time": "5:00 PM ET", "Team A": "Portugal", "Team B": "Croatia", "Status": "Finished", "Winner": "Portugal"},
    {"Match ID": 1016, "Group": "R32", "Date": "2026-07-03", "Time": "2:00 PM ET", "Team A": "Australia", "Team B": "Egypt", "Status": "Finished", "Winner": "Egypt"},
]


def build_round_of_16_prediction_matches():
    winners = []
    for index, row in enumerate(ROUND_OF_32_PREDICTION_MATCHES, start=1):
        winner = str(row.get("Winner", "")).strip()
        winners.append(winner or f"Winner R32-{index}")

    matches = []
    for pair_index in range(0, len(winners), 2):
        if pair_index + 1 >= len(winners):
            continue
        matches.append(
            {
                "Match ID": 2001 + (pair_index // 2),
                "Group": "R16",
                "Date": "",
                "Time": "",
                "Team A": winners[pair_index],
                "Team B": winners[pair_index + 1],
                "Status": "Upcoming",
                "Winner": "",
            }
        )
    return matches


def build_prediction_match_catalog(group_matches_df):
    r32_matches = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES)
    r16_matches = pd.DataFrame(build_round_of_16_prediction_matches())
    return pd.concat([r32_matches, r16_matches], ignore_index=True)
