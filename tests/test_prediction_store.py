import pandas as pd

from prediction_store import load_predictions, save_prediction, save_predictions


def test_prediction_survives_reload_from_sqlite(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"

    save_prediction("Ralph", 7, "Brazil", db_path=db_path)

    loaded = load_predictions(db_path=db_path)
    assert loaded.to_dict("records") == [
        {
            "Player": "Ralph",
            "Match ID": 7,
            "Predicted Winner": "Brazil",
            "Correct": "",
        }
    ]


def test_prediction_for_same_player_and_match_updates_without_duplicate(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"

    save_prediction("Ralph", 7, "Brazil", db_path=db_path)
    save_prediction("Ralph", 7, "France", db_path=db_path)

    loaded = load_predictions(db_path=db_path)
    assert len(loaded) == 1
    assert loaded.iloc[0]["Predicted Winner"] == "France"


def test_save_predictions_replaces_store_contents(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    save_prediction("Ralph", 7, "Brazil", db_path=db_path)

    save_predictions(
        pd.DataFrame(
            [
                {
                    "Player": "Ava",
                    "Match ID": 8,
                    "Predicted Winner": "Spain",
                    "Correct": "✅",
                }
            ]
        ),
        db_path=db_path,
    )

    loaded = load_predictions(db_path=db_path)
    assert loaded.to_dict("records") == [
        {
            "Player": "Ava",
            "Match ID": 8,
            "Predicted Winner": "Spain",
            "Correct": "✅",
        }
    ]
