import pandas as pd

from bracket_store import load_bracket, save_bracket_round
from prediction_store import load_predictions, save_predictions
from seed_restore import (
    R16_PREDICTIONS_RESET_MARKER,
    load_bracket_seed,
    load_prediction_seed,
    _restore_marker_exists,
    repair_bracket_store_from_seed,
    repair_prediction_store_from_seed,
    reset_prediction_match_ids_once,
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


def test_repair_prediction_store_from_seed_backfills_missing_rows_without_overwriting(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    seed_path = tmp_path / "predictions_seed.tsv"
    seed_path.write_text(
        "Player\tMatch ID\tPredicted Winner\tCorrect\n"
        "Ralph\t1005\tNorway\t✅\n"
        "Ralph\t1006\tFrance\t✅\n",
        encoding="utf-8",
    )
    save_predictions(
        pd.DataFrame(
            [
                {
                    "Player": "Ava",
                    "Match ID": 8,
                    "Predicted Winner": "Spain",
                    "Correct": "✅",
                },
                {
                    "Player": "Ralph",
                    "Match ID": 1005,
                    "Predicted Winner": "Norway",
                    "Correct": "✅",
                },
            ]
        ),
        db_path=db_path,
    )

    repaired = repair_prediction_store_from_seed(
        load_predictions(db_path=db_path),
        should_seed=True,
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        seed_path=seed_path,
    )

    assert repaired.to_dict("records") == [
        {
            "Player": "Ava",
            "Match ID": 8,
            "Predicted Winner": "Spain",
            "Correct": "✅",
        },
        {
            "Player": "Ralph",
            "Match ID": 1005,
            "Predicted Winner": "Norway",
            "Correct": "✅",
        },
        {
            "Player": "Ralph",
            "Match ID": 1006,
            "Predicted Winner": "France",
            "Correct": "✅",
        },
    ]


def test_reset_prediction_match_ids_once_clears_old_round_of_16_rows_and_writes_marker(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    save_predictions(
        pd.DataFrame(
            [
                {
                    "Player": "Ralph",
                    "Match ID": 1005,
                    "Predicted Winner": "Norway",
                    "Correct": "✅",
                },
                {
                    "Player": "Ralph",
                    "Match ID": 2002,
                    "Predicted Winner": "Morocco",
                    "Correct": "",
                },
            ]
        ),
        db_path=db_path,
    )

    reset = reset_prediction_match_ids_once(
        load_predictions(db_path=db_path),
        should_seed=True,
        match_ids=range(2001, 2009),
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        db_path=db_path,
    )

    assert reset.to_dict("records") == [
        {
            "Player": "Ralph",
            "Match ID": 1005,
            "Predicted Winner": "Norway",
            "Correct": "✅",
        }
    ]
    assert _restore_marker_exists(db_path, R16_PREDICTIONS_RESET_MARKER)


def test_reset_prediction_match_ids_once_skips_after_marker_exists(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    save_predictions(
        pd.DataFrame(
            [
                {
                    "Player": "Ralph",
                    "Match ID": 2002,
                    "Predicted Winner": "Morocco",
                    "Correct": "",
                }
            ]
        ),
        db_path=db_path,
    )

    reset_prediction_match_ids_once(
        load_predictions(db_path=db_path),
        should_seed=True,
        match_ids=range(2001, 2009),
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        db_path=db_path,
    )

    save_predictions(
        pd.DataFrame(
            [
                {
                    "Player": "Ralph",
                    "Match ID": 2002,
                    "Predicted Winner": "Morocco",
                    "Correct": "",
                }
            ]
        ),
        db_path=db_path,
    )

    second = reset_prediction_match_ids_once(
        load_predictions(db_path=db_path),
        should_seed=True,
        match_ids=range(2001, 2009),
        save_predictions_fn=lambda df: save_predictions(df, db_path=db_path),
        load_predictions_fn=lambda: load_predictions(db_path=db_path),
        db_path=db_path,
    )

    assert second.to_dict("records") == [
        {
            "Player": "Ralph",
            "Match ID": 2002,
            "Predicted Winner": "Morocco",
            "Correct": "",
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


def test_repair_bracket_store_from_seed_backfills_missing_rows_and_finished_results(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"
    seed_path = tmp_path / "bracket_seed.tsv"
    seed_path.write_text(
        "Match\tTeam A\tTeam B\tStatus\tWinner\n"
        "R32-1\tSouth Africa\tCanada\tFinished\tCanada\n"
        "R32-2\tBrazil\tJapan\tFinished\tBrazil\n",
        encoding="utf-8",
    )
    save_bracket_round(
        pd.DataFrame(
            [
                {
                    "Match": "R32-1",
                    "Team A": "South Africa",
                    "Team B": "Canada",
                    "Status": "Upcoming",
                    "Winner": "South Africa",
                }
            ]
        ),
        db_path=db_path,
    )

    repaired = repair_bracket_store_from_seed(
        load_bracket(db_path=db_path),
        should_seed=True,
        save_bracket_round_fn=lambda df: save_bracket_round(df, db_path=db_path),
        load_bracket_fn=lambda: load_bracket(db_path=db_path),
        seed_path=seed_path,
    )

    assert repaired.to_dict("records") == [
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
            "Status": "Finished",
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


def test_shipped_prediction_seed_contains_ralph_full_round_of_32_picks():
    seeded = load_prediction_seed()
    ralph_r32 = seeded[
        (seeded["Player"] == "Ralph")
        & seeded["Match ID"].between(1001, 1016)
    ]
    winners_by_match = dict(zip(ralph_r32["Match ID"], ralph_r32["Predicted Winner"]))

    assert winners_by_match == {
        1001: "Canada",
        1002: "Brazil",
        1003: "Paraguay",
        1004: "Netherlands",
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
        1016: "Australia",
    }


def test_shipped_bracket_seed_contains_r32_winners_needed_for_round_of_16():
    seeded = load_bracket_seed().set_index("Match")

    assert seeded["Winner"].to_dict() == {
        "R32-1": "Canada",
        "R32-2": "Brazil",
        "R32-3": "Paraguay",
        "R32-4": "Morocco",
        "R32-5": "Norway",
        "R32-6": "France",
        "R32-7": "Mexico",
        "R32-8": "England",
        "R32-9": "Belgium",
        "R32-10": "United States",
        "R32-11": "Switzerland",
        "R32-12": "Spain",
        "R32-13": "Argentina",
        "R32-14": "Colombia",
        "R32-15": "Portugal",
        "R32-16": "Egypt",
    }
