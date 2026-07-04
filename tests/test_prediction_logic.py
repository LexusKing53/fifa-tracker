import pandas as pd

from prediction_logic import (
    filter_predictions_to_catalog,
    prediction_result_for_pick,
    score_predictions,
)


def test_score_predictions_marks_finished_round_of_32_pick_correct():
    predictions = pd.DataFrame(
        [
            {
                "Player": "Ralph",
                "Match ID": 1002,
                "Predicted Winner": "Brazil",
                "Correct": "",
            }
        ]
    )
    match_catalog = pd.DataFrame(
        [
            {
                "Match ID": 1002,
                "Status": "Finished",
                "Winner": "Brazil",
            }
        ]
    )

    scored = score_predictions(predictions, match_catalog)

    assert scored.iloc[0]["Correct"] == "✅"


def test_score_predictions_clears_stale_results_for_missing_catalog_matches():
    predictions = pd.DataFrame(
        [
            {
                "Player": "Ralph",
                "Match ID": 1,
                "Predicted Winner": "Mexico",
                "Correct": "✅",
            }
        ]
    )
    match_catalog = pd.DataFrame(
        [
            {
                "Match ID": 1002,
                "Status": "Finished",
                "Winner": "Brazil",
            }
        ]
    )

    scored = score_predictions(predictions, match_catalog)

    assert scored.iloc[0]["Correct"] == ""


def test_filter_predictions_to_catalog_excludes_finished_group_stage_rows():
    predictions = pd.DataFrame(
        [
            {
                "Player": "Ralph",
                "Match ID": 1,
                "Predicted Winner": "Mexico",
                "Correct": "✅",
            },
            {
                "Player": "Ralph",
                "Match ID": 1002,
                "Predicted Winner": "Brazil",
                "Correct": "✅",
            },
        ]
    )
    match_catalog = pd.DataFrame([{"Match ID": 1002}])

    filtered = filter_predictions_to_catalog(predictions, match_catalog)

    assert filtered["Match ID"].tolist() == [1002]


def test_prediction_result_for_pick_returns_check_for_finished_correct_pick():
    match_catalog = pd.DataFrame(
        [
            {
                "Match ID": 1002,
                "Status": "Finished",
                "Winner": "Brazil",
            }
        ]
    )

    assert prediction_result_for_pick(match_catalog, 1002, "Brazil") == "✅"


def test_prediction_result_for_pick_marks_draw_pick_wrong_when_knockout_has_winner():
    match_catalog = pd.DataFrame(
        [
            {
                "Match ID": 2001,
                "Status": "Finished",
                "Winner": "Canada",
            }
        ]
    )

    assert prediction_result_for_pick(match_catalog, 2001, "Draw") == "❌"
