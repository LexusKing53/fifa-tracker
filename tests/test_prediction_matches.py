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
    assert catalog.loc[2001, "Team A"] == "Paraguay"
    assert catalog.loc[2001, "Team B"] == "France"
    assert catalog.loc[2002, "Team A"] == "Morocco"
    assert catalog.loc[2002, "Team B"] == "Canada"
    assert catalog.loc[2003, "Team A"] == "Portugal"
    assert catalog.loc[2003, "Team B"] == "Spain"
    assert catalog.loc[2004, "Team A"] == "Brazil"
    assert catalog.loc[2004, "Team B"] == "Norway"
    assert catalog.loc[2005, "Team A"] == "Argentina"
    assert catalog.loc[2005, "Team B"] == "Egypt"
    assert catalog.loc[2006, "Team A"] == "Switzerland"
    assert catalog.loc[2006, "Team B"] == "Colombia"
    assert catalog.loc[2007, "Team A"] == "United States"
    assert catalog.loc[2007, "Team B"] == "Belgium"
    assert catalog.loc[2008, "Group"] == "R16"
    assert catalog.loc[2008, "Team A"] == "Mexico"
    assert catalog.loc[2008, "Team B"] == "England"
    assert catalog.loc[2001, "Status"] == "Finished"
    assert catalog.loc[2001, "Winner"] == "France"
    assert catalog.loc[2008, "Winner"] == ""


def test_prediction_catalog_marks_finished_round_of_16_matches():
    catalog = build_prediction_match_catalog(pd.DataFrame()).set_index("Match ID")

    assert catalog.loc[2001, "Status"] == "Finished"
    assert catalog.loc[2001, "Winner"] == "France"
    assert catalog.loc[2002, "Status"] == "Finished"
    assert catalog.loc[2002, "Winner"] == "Morocco"


def test_prediction_catalog_uses_supplied_live_round_of_16_results():
    live_matches = pd.DataFrame(
        [
            {
                "Team A": "Portugal",
                "Team B": "Spain",
                "Status": "Finished",
                "Winner": "Spain",
            }
        ]
    )

    catalog = build_prediction_match_catalog(live_matches).set_index("Match ID")

    assert catalog.loc[2003, "Status"] == "Finished"
    assert catalog.loc[2003, "Winner"] == "Spain"


def test_prediction_catalog_builds_quarterfinal_matches_from_finished_round_of_16():
    live_matches = pd.DataFrame(
        [
            {"Team A": "Paraguay", "Team B": "France", "Status": "Finished", "Winner": "France"},
            {"Team A": "Morocco", "Team B": "Canada", "Status": "Finished", "Winner": "Morocco"},
            {"Team A": "Portugal", "Team B": "Spain", "Status": "Finished", "Winner": "Spain"},
            {"Team A": "Brazil", "Team B": "Norway", "Status": "Finished", "Winner": "Norway"},
            {"Team A": "Argentina", "Team B": "Egypt", "Status": "Finished", "Winner": "Argentina"},
            {"Team A": "Switzerland", "Team B": "Colombia", "Status": "Finished", "Winner": "Switzerland"},
            {"Team A": "United States", "Team B": "Belgium", "Status": "Finished", "Winner": "Belgium"},
            {"Team A": "Mexico", "Team B": "England", "Status": "Finished", "Winner": "England"},
        ]
    )

    catalog = build_prediction_match_catalog(live_matches).set_index("Match ID")

    assert catalog.loc[3001, "Group"] == "QF"
    assert catalog.loc[3001, "Team A"] == "France"
    assert catalog.loc[3001, "Team B"] == "Morocco"
    assert catalog.loc[3002, "Team A"] == "Spain"
    assert catalog.loc[3002, "Team B"] == "Belgium"
    assert catalog.loc[3003, "Team A"] == "Norway"
    assert catalog.loc[3003, "Team B"] == "England"
    assert catalog.loc[3004, "Team A"] == "Argentina"
    assert catalog.loc[3004, "Team B"] == "Switzerland"
    assert catalog.loc[3001, "Status"] == "Upcoming"
    assert catalog.loc[3001, "Winner"] == ""


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
