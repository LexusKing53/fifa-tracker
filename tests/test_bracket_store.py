import pandas as pd

from bracket_store import clear_bracket, load_bracket, restore_bracket_round, save_bracket_round


def test_save_bracket_round_survives_reload(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    round_df = pd.DataFrame(
        [
            {
                "Match": "R32-2",
                "Team A": "Brazil",
                "Team B": "Japan",
                "Status": "Upcoming",
                "Winner": "Brazil",
            }
        ]
    )

    save_bracket_round(round_df, db_path=db_path)

    loaded = load_bracket(db_path=db_path)
    assert loaded.to_dict("records") == round_df.to_dict("records")


def test_restore_bracket_round_keeps_saved_winner_for_same_matchup():
    expected_round = pd.DataFrame(
        [
            {
                "Match": "R32-2",
                "Team A": "Brazil",
                "Team B": "Japan",
                "Status": "Upcoming",
                "Winner": "",
            }
        ]
    )
    saved_round = pd.DataFrame(
        [
            {
                "Match": "R32-2",
                "Team A": "Brazil",
                "Team B": "Japan",
                "Status": "Upcoming",
                "Winner": "Brazil",
            }
        ]
    )

    restored = restore_bracket_round(expected_round, saved_round)

    assert restored.iloc[0]["Winner"] == "Brazil"


def test_restore_bracket_round_clears_saved_winner_when_matchup_changes():
    expected_round = pd.DataFrame(
        [
            {
                "Match": "R32-2",
                "Team A": "Brazil",
                "Team B": "Morocco",
                "Status": "Upcoming",
                "Winner": "",
            }
        ]
    )
    saved_round = pd.DataFrame(
        [
            {
                "Match": "R32-2",
                "Team A": "Brazil",
                "Team B": "Japan",
                "Status": "Upcoming",
                "Winner": "Brazil",
            }
        ]
    )

    restored = restore_bracket_round(expected_round, saved_round)

    assert restored.iloc[0]["Winner"] == ""


def test_clear_bracket_deletes_saved_rows(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    round_df = pd.DataFrame(
        [
            {
                "Match": "R32-2",
                "Team A": "Brazil",
                "Team B": "Japan",
                "Status": "Upcoming",
                "Winner": "Brazil",
            }
        ]
    )
    save_bracket_round(round_df, db_path=db_path)

    clear_bracket(db_path=db_path)

    loaded = load_bracket(db_path=db_path)
    assert loaded.empty
