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


ROUND_OF_16_PAIRINGS = [
    {"Match ID": 2001, "Left R32 Match ID": 1003, "Right R32 Match ID": 1006},
    {"Match ID": 2002, "Left R32 Match ID": 1004, "Right R32 Match ID": 1001},
    {"Match ID": 2003, "Left R32 Match ID": 1015, "Right R32 Match ID": 1012},
    {"Match ID": 2004, "Left R32 Match ID": 1002, "Right R32 Match ID": 1005},
    {"Match ID": 2005, "Left R32 Match ID": 1013, "Right R32 Match ID": 1016},
    {"Match ID": 2006, "Left R32 Match ID": 1011, "Right R32 Match ID": 1014},
    {"Match ID": 2007, "Left R32 Match ID": 1010, "Right R32 Match ID": 1009},
    {"Match ID": 2008, "Left R32 Match ID": 1007, "Right R32 Match ID": 1008},
]


ROUND_OF_16_RESULT_OVERRIDES = {
    2002: {"Status": "Finished", "Winner": "Morocco"},
}


def build_round_of_16_from_round_of_32(round_of_32_df):
    round_of_32 = round_of_32_df.copy()
    if len(round_of_32) == 0:
        return pd.DataFrame(
            columns=["Match", "Match ID", "Group", "Date", "Time", "Team A", "Team B", "Status", "Winner"]
        )

    matches_by_id = round_of_32.drop_duplicates(subset=["Match ID"]).set_index("Match ID")

    matches = []
    for index, pairing in enumerate(ROUND_OF_16_PAIRINGS, start=1):
        left_id = pairing["Left R32 Match ID"]
        right_id = pairing["Right R32 Match ID"]
        if left_id not in matches_by_id.index or right_id not in matches_by_id.index:
            continue

        left_row = matches_by_id.loc[left_id]
        right_row = matches_by_id.loc[right_id]
        left_winner = str(left_row.get("Winner", "")).strip()
        right_winner = str(right_row.get("Winner", "")).strip()
        result_override = ROUND_OF_16_RESULT_OVERRIDES.get(pairing["Match ID"], {})
        team_a = left_winner or f"Winner R32-{left_id - 1000}"
        team_b = right_winner or f"Winner R32-{right_id - 1000}"
        status = str(result_override.get("Status", "Upcoming")).strip() or "Upcoming"
        winner = str(result_override.get("Winner", "")).strip()
        if status != "Finished" or winner not in {team_a, team_b}:
            status = "Upcoming"
            winner = ""

        matches.append(
            {
                "Match": f"R16-{index}",
                "Match ID": pairing["Match ID"],
                "Group": "R16",
                "Date": "",
                "Time": "",
                "Team A": team_a,
                "Team B": team_b,
                "Status": status,
                "Winner": winner,
            }
        )
    return pd.DataFrame(matches)


def build_round_of_16_prediction_matches():
    round_of_32 = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES)
    return build_round_of_16_from_round_of_32(round_of_32)


def build_prediction_match_catalog(group_matches_df):
    r32_matches = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES)
    r16_matches = build_round_of_16_prediction_matches()
    return pd.concat([r32_matches, r16_matches], ignore_index=True)
