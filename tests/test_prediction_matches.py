import pandas as pd

from prediction_matches import build_prediction_match_catalog


def test_prediction_catalog_hides_finished_group_matches_and_keeps_round_of_32():
    matches = pd.DataFrame(
        [
            {
                "Match ID": 1,
                "Group": "A",
                "Date": "2026-06-11",
                "Time": "3:00 PM ET",
                "Team A": "Mexico",
                "Team B": "South Africa",
                "Status": "Finished",
                "Winner": "Mexico",
            },
            {
                "Match ID": 73,
                "Group": "M",
                "Date": "2026-07-10",
                "Time": "8:00 PM ET",
                "Team A": "Team 1",
                "Team B": "Team 2",
                "Status": "Upcoming",
                "Winner": "",
            },
        ]
    )

    catalog = build_prediction_match_catalog(matches)

    assert 1 not in catalog["Match ID"].tolist()
    assert 73 in catalog["Match ID"].tolist()
    assert 1002 in catalog["Match ID"].tolist()


def test_prediction_catalog_marks_brazil_round_of_32_win_as_finished():
    catalog = build_prediction_match_catalog(pd.DataFrame())
    brazil_match = catalog.loc[catalog["Match ID"] == 1002].iloc[0]

    assert brazil_match["Team A"] == "Brazil"
    assert brazil_match["Team B"] == "Japan"
    assert brazil_match["Status"] == "Finished"
    assert brazil_match["Winner"] == "Brazil"
