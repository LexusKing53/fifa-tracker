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
    assert 1002 in catalog["Match ID"].tolist()
    assert 73 not in catalog["Match ID"].tolist()


def test_prediction_catalog_adds_round_of_16_matches():
    catalog = build_prediction_match_catalog(pd.DataFrame()).set_index("Match ID")

    assert catalog.loc[2001, "Group"] == "R16"
    assert catalog.loc[2001, "Team A"] == "Canada"
    assert catalog.loc[2001, "Team B"] == "Brazil"
    assert catalog.loc[2008, "Group"] == "R16"
    assert catalog.loc[2008, "Team A"] == "Portugal"
    assert catalog.loc[2008, "Team B"] == "Egypt"
    assert catalog.loc[2001, "Status"] == "Upcoming"
    assert catalog.loc[2008, "Winner"] == ""


def test_prediction_catalog_marks_brazil_round_of_32_win_as_finished():
    catalog = build_prediction_match_catalog(pd.DataFrame())
    brazil_match = catalog.loc[catalog["Match ID"] == 1002].iloc[0]

    assert brazil_match["Team A"] == "Brazil"
    assert brazil_match["Team B"] == "Japan"
    assert brazil_match["Status"] == "Finished"
    assert brazil_match["Winner"] == "Brazil"


def test_prediction_catalog_marks_all_completed_round_of_32_matches_as_finished():
    catalog = build_prediction_match_catalog(pd.DataFrame())
    round_of_32 = catalog[catalog["Group"] == "R32"].set_index("Match ID")

    assert round_of_32["Status"].to_dict() == {
        1001: "Finished",
        1002: "Finished",
        1003: "Finished",
        1004: "Finished",
        1005: "Finished",
        1006: "Finished",
        1007: "Finished",
        1008: "Finished",
        1009: "Finished",
        1010: "Finished",
        1011: "Finished",
        1012: "Finished",
        1013: "Finished",
        1014: "Finished",
        1015: "Finished",
        1016: "Finished",
    }
    assert round_of_32["Winner"].to_dict() == {
        1001: "Canada",
        1002: "Brazil",
        1003: "Paraguay",
        1004: "Morocco",
        1005: "Norway",
        1006: "France",
        1007: "Mexico",
        1008: "England",
        1009: "Belgium",
        1010: "United States",
        1011: "Switzerland",
        1012: "Spain",
        1013: "Argentina",
        1014: "Colombia",
        1015: "Portugal",
        1016: "Egypt",
    }


def test_prediction_catalog_keeps_round_of_32_kickoff_data_for_locking():
    catalog = build_prediction_match_catalog(pd.DataFrame()).set_index("Match ID")

    assert catalog.loc[1005, "Date"] == "2026-06-30"
    assert catalog.loc[1005, "Time"] == "1:00 PM ET"
    assert catalog.loc[1010, "Date"] == "2026-07-01"
    assert catalog.loc[1010, "Time"] == "8:00 PM ET"
    assert catalog.loc[1016, "Date"] == "2026-07-03"
    assert catalog.loc[1016, "Time"] == "2:00 PM ET"
