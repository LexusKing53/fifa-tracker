import pandas as pd

from bracket_store import load_bracket, save_bracket_round
from prediction_store import load_predictions, save_predictions
from seed_restore import (
    _restore_marker_exists,
    restore_bracket_store_if_missing,
    restore_prediction_store_if_missing,
)


def test_restore_prediction_store_if_missing_seeds_fresh_store(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    seed_path = tmp_path / "predictions_seed.tsv"
    seed_path.write_text(
        "Player\tMatch ID\tPredicted Winner\tCorrect\n"
        "Ralph\t21\tUnited States\t\n"
        "Ralph\t22\tParaguay\t❌\n",
        encoding="utf-8",
    )

    restored = restore_prediction_store_if_missing(
        load_predictions(db_path=db_path),
        should_seed=True,
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        seed_path=seed_path,
        db_path=db_path,
    )

    assert restored.to_dict("records") == [
        {
            "Player": "Ralph",
            "Match ID": 21,
            "Predicted Winner": "United States",
            "Correct": "",
        },
        {
            "Player": "Ralph",
            "Match ID": 22,
            "Predicted Winner": "Paraguay",
            "Correct": "❌",
        },
    ]


def test_restore_prediction_store_if_missing_preserves_existing_rows(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
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

    restored = restore_prediction_store_if_missing(
        load_predictions(db_path=db_path),
        should_seed=True,
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        seed_path=tmp_path / "missing.tsv",
        db_path=db_path,
    )

    assert restored.to_dict("records") == [
        {
            "Player": "Ava",
            "Match ID": 8,
            "Predicted Winner": "Spain",
            "Correct": "✅",
        }
    ]


def test_restore_bracket_store_if_missing_seeds_fresh_store(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    seed_path = tmp_path / "bracket_seed.tsv"
    seed_path.write_text(
        "Match\tTeam A\tTeam B\tStatus\tWinner\n"
        "R32-1\tSouth Africa\tCanada\tFinished\tCanada\n"
        "R32-2\tBrazil\tJapan\tUpcoming\tBrazil\n",
        encoding="utf-8",
    )

    restored = restore_bracket_store_if_missing(
        load_bracket(db_path=db_path),
        should_seed=True,
        save_bracket_round_fn=lambda df: save_bracket_round(df, db_path=db_path),
        load_bracket_fn=lambda: load_bracket(db_path=db_path),
        seed_path=seed_path,
        db_path=db_path,
    )

    assert restored.to_dict("records") == [
        {
            "Match": "R32-1",
            "Team A": "South Africa",
            "Team B": "Canada",
            "Status": "Finished",
            "Winner": "Canada",
        },
        {
            "Match": "R32-2",
            "Team A": "Brazil",
            "Team B": "Japan",
            "Status": "Upcoming",
            "Winner": "Brazil",
        },
    ]


def test_restore_bracket_store_if_missing_skips_when_not_bootstrapping(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    existing = load_bracket(db_path=db_path)

    restored = restore_bracket_store_if_missing(
        existing,
        should_seed=False,
        save_bracket_round_fn=lambda df: save_bracket_round(df, db_path=db_path),
        load_bracket_fn=lambda: load_bracket(db_path=db_path),
        seed_path=tmp_path / "missing.tsv",
        db_path=db_path,
    )

    assert restored.empty


def test_restore_prediction_store_if_missing_seeds_existing_empty_db_once(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    seed_path = tmp_path / "predictions_seed.tsv"
    seed_path.write_text(
        "Player\tMatch ID\tPredicted Winner\tCorrect\n"
        "Ralph\t1005\tNorway\t\n"
        "Ralph\t1006\tFrance\t\n",
        encoding="utf-8",
    )

    # Create the database file first to reproduce production: db exists but is empty.
    load_predictions(db_path=db_path)

    restored = restore_prediction_store_if_missing(
        load_predictions(db_path=db_path),
        should_seed=True,
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        seed_path=seed_path,
        db_path=db_path,
    )

    assert restored.to_dict("records") == [
        {
            "Player": "Ralph",
            "Match ID": 1005,
            "Predicted Winner": "Norway",
            "Correct": "",
        },
        {
            "Player": "Ralph",
            "Match ID": 1006,
            "Predicted Winner": "France",
            "Correct": "",
        },
    ]
    assert _restore_marker_exists(db_path, "predictions_seed_restored_v1")


def test_restore_prediction_store_if_missing_respects_existing_restore_marker(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    seed_path = tmp_path / "predictions_seed.tsv"
    seed_path.write_text(
        "Player\tMatch ID\tPredicted Winner\tCorrect\n"
        "Ralph\t1005\tNorway\t\n",
        encoding="utf-8",
    )

    # First restore writes the marker.
    restore_prediction_store_if_missing(
        load_predictions(db_path=db_path),
        should_seed=True,
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        seed_path=seed_path,
        db_path=db_path,
    )

    # Simulate a later empty store after the one-time restore already happened.
    save_predictions(pd.DataFrame(columns=["Player", "Match ID", "Predicted Winner", "Correct"]), db_path=db_path)
    restored = restore_prediction_store_if_missing(
        load_predictions(db_path=db_path),
        should_seed=True,
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        seed_path=seed_path,
        db_path=db_path,
    )

    assert restored.empty
