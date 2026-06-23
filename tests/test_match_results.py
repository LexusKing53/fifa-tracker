import pandas as pd

from match_results import apply_known_final_results, build_standings


def test_spain_cape_verde_zero_zero_draw_is_finished_and_scores_one_point_each():
    matches = pd.DataFrame([
        {
            "Match ID": 43,
            "Group": "H",
            "Date": "2026-06-15",
            "Time": "12:00 PM ET",
            "Team A": "Spain",
            "Team B": "Cape Verde",
            "Team A Score": "",
            "Team B Score": "",
            "Winner": "",
            "Loser": "",
            "Status": "Upcoming",
            "Venue": "Atlanta Stadium",
        },
        {
            "Match ID": 44,
            "Group": "H",
            "Date": "2026-06-15",
            "Time": "6:00 PM ET",
            "Team A": "Saudi Arabia",
            "Team B": "Uruguay",
            "Team A Score": "",
            "Team B Score": "",
            "Winner": "",
            "Loser": "",
            "Status": "Upcoming",
            "Venue": "Miami Stadium",
        },
    ])

    updated = apply_known_final_results(matches)
    result = updated.loc[updated["Match ID"] == 43].iloc[0]

    assert result["Team A Score"] == "0"
    assert result["Team B Score"] == "0"
    assert result["Winner"] == "Draw"
    assert result["Loser"] == "Draw"
    assert result["Status"] == "Finished"
    assert 43 not in updated[updated["Status"] != "Finished"]["Match ID"].tolist()

    standings = build_standings(updated).set_index("Team")

    assert standings.loc["Spain", "P"] == 1
    assert standings.loc["Spain", "D"] == 1
    assert standings.loc["Spain", "Pts"] == 1
    assert standings.loc["Cape Verde", "P"] == 1
    assert standings.loc["Cape Verde", "D"] == 1
    assert standings.loc["Cape Verde", "Pts"] == 1


def test_uruguay_cape_verde_zero_zero_draw_is_finished_and_scores_one_point_each():
    matches = pd.DataFrame([
        {
            "Match ID": 46,
            "Group": "H",
            "Date": "2026-06-21",
            "Time": "6:00 PM ET",
            "Team A": "Uruguay",
            "Team B": "Cape Verde",
            "Team A Score": "",
            "Team B Score": "",
            "Winner": "",
            "Loser": "",
            "Status": "Upcoming",
            "Venue": "Miami Stadium",
        },
    ])

    updated = apply_known_final_results(matches)
    result = updated.loc[updated["Match ID"] == 46].iloc[0]

    assert result["Team A Score"] == "0"
    assert result["Team B Score"] == "0"
    assert result["Winner"] == "Draw"
    assert result["Loser"] == "Draw"
    assert result["Status"] == "Finished"
    assert 46 not in updated[updated["Status"] != "Finished"]["Match ID"].tolist()

    standings = build_standings(updated).set_index("Team")

    assert standings.loc["Uruguay", "P"] == 1
    assert standings.loc["Uruguay", "D"] == 1
    assert standings.loc["Uruguay", "Pts"] == 1
    assert standings.loc["Cape Verde", "P"] == 1
    assert standings.loc["Cape Verde", "D"] == 1
    assert standings.loc["Cape Verde", "Pts"] == 1
