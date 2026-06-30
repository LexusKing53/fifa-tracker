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


def test_prediction_catalog_marks_all_completed_round_of_32_matches_as_finished():
    catalog = build_prediction_match_catalog(pd.DataFrame()).set_index("Match ID")

    assert catalog.loc[1001, "Status"] == "Finished"
    assert catalog.loc[1001, "Winner"] == "Canada"
    assert catalog.loc[1002, "Status"] == "Finished"
    assert catalog.loc[1002, "Winner"] == "Brazil"
    assert catalog.loc[1003, "Status"] == "Finished"
    assert catalog.loc[1003, "Winner"] == "Paraguay"
    assert catalog.loc[1004, "Status"] == "Finished"
    assert catalog.loc[1004, "Winner"] == "Morocco"


def test_prediction_catalog_keeps_round_of_32_kickoff_data_for_locking():
    catalog = build_prediction_match_catalog(pd.DataFrame()).set_index("Match ID")

    assert catalog.loc[1005, "Date"] == "2026-06-30"
    assert catalog.loc[1005, "Time"] == "1:00 PM ET"
    assert catalog.loc[1010, "Date"] == "2026-07-01"
    assert catalog.loc[1010, "Time"] == "8:00 PM ET"
    assert catalog.loc[1016, "Date"] == "2026-07-03"
    assert catalog.loc[1016, "Time"] == "2:00 PM ET"
