import sqlite3
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent
PREDICTION_SEED_PATH = ROOT / "recovery" / "predictions_seed.tsv"
BRACKET_SEED_PATH = ROOT / "recovery" / "bracket_seed.tsv"
DEFAULT_DB_PATH = ROOT / "predictions.sqlite3"

PREDICTION_COLUMNS = ["Player", "Match ID", "Predicted Winner", "Correct"]
BRACKET_COLUMNS = ["Match", "Team A", "Team B", "Status", "Winner"]
PREDICTIONS_RESTORE_MARKER = "predictions_seed_restored_v1"
BRACKET_RESTORE_MARKER = "bracket_seed_restored_v1"
R16_PREDICTIONS_RESET_MARKER = "round_of_16_predictions_reset_v2"


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


def _connect_marker_db(db_path=DEFAULT_DB_PATH):
    conn = sqlite3.connect(Path(db_path))
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS restore_markers (
            marker TEXT NOT NULL PRIMARY KEY,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def _restore_marker_exists(db_path, marker):
    with _connect_marker_db(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM restore_markers WHERE marker = ?",
            (str(marker),),
        ).fetchone()
    return row is not None


def _write_restore_marker(db_path, marker):
    with _connect_marker_db(db_path) as conn:
        conn.execute(
            """
            INSERT INTO restore_markers (marker, updated_at)
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(marker) DO UPDATE SET
                updated_at = CURRENT_TIMESTAMP
            """,
            (str(marker),),
        )


def restore_prediction_store_if_missing(
    predictions,
    *,
    should_seed,
    save_predictions_fn,
    load_predictions_fn,
    seed_path=PREDICTION_SEED_PATH,
    db_path=DEFAULT_DB_PATH,
):
    if not should_seed or len(predictions) > 0:
        return predictions
    if _restore_marker_exists(db_path, PREDICTIONS_RESTORE_MARKER):
        return predictions

    seeded = load_prediction_seed(seed_path)
    if len(seeded) == 0:
        return predictions

    save_predictions_fn(seeded)
    _write_restore_marker(db_path, PREDICTIONS_RESTORE_MARKER)
    return load_predictions_fn()


def repair_prediction_store_from_seed(
    predictions,
    *,
    should_seed,
    save_predictions_fn,
    load_predictions_fn,
    seed_path=PREDICTION_SEED_PATH,
):
    if not should_seed:
        return predictions

    seeded = load_prediction_seed(seed_path)
    if len(seeded) == 0:
        return predictions
    if len(predictions) == 0:
        save_predictions_fn(seeded)
        return load_predictions_fn()

    existing_keys = predictions[["Player", "Match ID"]].drop_duplicates()
    missing = seeded.merge(
        existing_keys,
        on=["Player", "Match ID"],
        how="left",
        indicator=True,
    )
    missing = missing[missing["_merge"] == "left_only"][PREDICTION_COLUMNS].copy()
    if len(missing) == 0:
        return predictions

    merged = pd.concat([predictions, missing], ignore_index=True)
    save_predictions_fn(merged[PREDICTION_COLUMNS])
    return load_predictions_fn()


def reset_prediction_match_ids_once(
    predictions,
    *,
    should_seed,
    match_ids,
    save_predictions_fn,
    load_predictions_fn,
    db_path=DEFAULT_DB_PATH,
    marker=R16_PREDICTIONS_RESET_MARKER,
):
    if not should_seed:
        return predictions
    if _restore_marker_exists(db_path, marker):
        return predictions

    filtered = predictions.copy()
    if len(filtered) > 0:
        filtered = filtered[~filtered["Match ID"].isin(match_ids)].copy()

    if not filtered.equals(predictions):
        save_predictions_fn(filtered)
        filtered = load_predictions_fn()

    _write_restore_marker(db_path, marker)
    return filtered


def restore_bracket_store_if_missing(
    saved_bracket,
    *,
    should_seed,
    save_bracket_round_fn,
    load_bracket_fn,
    seed_path=BRACKET_SEED_PATH,
    db_path=DEFAULT_DB_PATH,
):
    if not should_seed or len(saved_bracket) > 0:
        return saved_bracket
    if _restore_marker_exists(db_path, BRACKET_RESTORE_MARKER):
        return saved_bracket

    seeded = load_bracket_seed(seed_path)
    if len(seeded) == 0:
        return saved_bracket

    save_bracket_round_fn(seeded)
    _write_restore_marker(db_path, BRACKET_RESTORE_MARKER)
    return load_bracket_fn()


def repair_bracket_store_from_seed(
    saved_bracket,
    *,
    should_seed,
    save_bracket_round_fn,
    load_bracket_fn,
    seed_path=BRACKET_SEED_PATH,
):
    if not should_seed:
        return saved_bracket

    seeded = load_bracket_seed(seed_path)
    if len(seeded) == 0:
        return saved_bracket
    if len(saved_bracket) == 0:
        save_bracket_round_fn(seeded)
        return load_bracket_fn()

    repaired = saved_bracket.copy()
    repaired["Match"] = repaired["Match"].astype(str)
    changed = False

    for _, seed_row in seeded.iterrows():
        match_key = str(seed_row["Match"])
        existing = repaired[repaired["Match"] == match_key]
        if len(existing) == 0:
            repaired = pd.concat([repaired, pd.DataFrame([seed_row])], ignore_index=True)
            changed = True
            continue

        current = existing.iloc[0]
        seed_finished = str(seed_row.get("Status", "")).strip() == "Finished"
        current_team_a = str(current.get("Team A", "")).strip()
        current_team_b = str(current.get("Team B", "")).strip()
        current_status = str(current.get("Status", "")).strip()
        current_winner = str(current.get("Winner", "")).strip()
        seed_team_a = str(seed_row.get("Team A", "")).strip()
        seed_team_b = str(seed_row.get("Team B", "")).strip()
        seed_winner = str(seed_row.get("Winner", "")).strip()

        if not seed_finished:
            continue

        if (
            current_team_a != seed_team_a
            or current_team_b != seed_team_b
            or current_status != "Finished"
            or current_winner != seed_winner
        ):
            repaired = repaired[repaired["Match"] != match_key]
            repaired = pd.concat([repaired, pd.DataFrame([seed_row])], ignore_index=True)
            changed = True

    if not changed:
        return saved_bracket

    save_bracket_round_fn(repaired[BRACKET_COLUMNS])
    return load_bracket_fn()
