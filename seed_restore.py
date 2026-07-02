from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
PREDICTION_SEED_PATH = ROOT / "recovery" / "predictions_seed.tsv"
BRACKET_SEED_PATH = ROOT / "recovery" / "bracket_seed.tsv"

PREDICTION_COLUMNS = ["Player", "Match ID", "Predicted Winner", "Correct"]
BRACKET_COLUMNS = ["Match", "Team A", "Team B", "Status", "Winner"]


def _load_seed(seed_path, columns):
    path = Path(seed_path)
    if not path.exists():
        return pd.DataFrame(columns=columns)

    seeded = pd.read_csv(path, sep="\t").fillna("")
    for column in columns:
        if column not in seeded.columns:
            seeded[column] = ""
    return seeded[columns].copy()


def load_prediction_seed(seed_path=PREDICTION_SEED_PATH):
    seeded = _load_seed(seed_path, PREDICTION_COLUMNS)
    if "Match ID" in seeded.columns:
        seeded["Match ID"] = seeded["Match ID"].astype(int)
    return seeded


def load_bracket_seed(seed_path=BRACKET_SEED_PATH):
    return _load_seed(seed_path, BRACKET_COLUMNS)


def restore_prediction_store_if_missing(
    predictions,
    *,
    should_seed,
    save_predictions_fn,
    load_predictions_fn,
    seed_path=PREDICTION_SEED_PATH,
):
    if not should_seed or len(predictions) > 0:
        return predictions

    seeded = load_prediction_seed(seed_path)
    if len(seeded) == 0:
        return predictions

    save_predictions_fn(seeded)
    return load_predictions_fn()


def restore_bracket_store_if_missing(
    saved_bracket,
    *,
    should_seed,
    save_bracket_round_fn,
    load_bracket_fn,
    seed_path=BRACKET_SEED_PATH,
):
    if not should_seed or len(saved_bracket) > 0:
        return saved_bracket

    seeded = load_bracket_seed(seed_path)
    if len(seeded) == 0:
        return saved_bracket

    save_bracket_round_fn(seeded)
    return load_bracket_fn()
