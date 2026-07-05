import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

try:
    import libsql
except Exception:
    libsql = None

try:
    import streamlit as st
except Exception:
    st = None


PREDICTION_COLUMNS = ["Player", "Match ID", "Predicted Winner", "Correct"]
DEFAULT_DB_PATH = Path("predictions.sqlite3")


def _get_secret(name):
    value = os.environ.get(name, "")
    if value:
        return value
    if st is None:
        return ""
    try:
        return str(st.secrets.get(name, ""))
    except Exception:
        return ""


def _turso_config_for(db_path):
    if Path(db_path) != DEFAULT_DB_PATH or libsql is None:
        return None

    url = _get_secret("TURSO_DATABASE_URL")
    token = _get_secret("TURSO_AUTH_TOKEN")
    if not url or not token:
        return None
    return {"database": url, "auth_token": token}


def _open_connection(db_path=DEFAULT_DB_PATH):
    turso_config = _turso_config_for(db_path)
    if turso_config is not None:
        return libsql.connect(**turso_config)

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(path)


@contextmanager
def _connect(db_path=DEFAULT_DB_PATH):
    conn = _open_connection(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS predictions (
            player TEXT NOT NULL,
            match_id INTEGER NOT NULL,
            predicted_winner TEXT NOT NULL,
            correct TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (player, match_id)
        )
        """
    )
    try:
        yield conn
        commit = getattr(conn, "commit", None)
        if callable(commit):
            commit()
    except Exception:
        rollback = getattr(conn, "rollback", None)
        if callable(rollback):
            try:
                rollback()
            except Exception:
                pass
        raise
    finally:
        close = getattr(conn, "close", None)
        if callable(close):
            close()


def load_predictions(db_path=DEFAULT_DB_PATH):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT player, match_id, predicted_winner, correct
            FROM predictions
            ORDER BY player, match_id
            """
        ).fetchall()

    return pd.DataFrame(rows, columns=PREDICTION_COLUMNS)


def save_prediction(player, match_id, predicted_winner, correct="", db_path=DEFAULT_DB_PATH):
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO predictions (player, match_id, predicted_winner, correct, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(player, match_id) DO UPDATE SET
                predicted_winner = excluded.predicted_winner,
                correct = excluded.correct,
                updated_at = CURRENT_TIMESTAMP
            """,
            (str(player), int(match_id), str(predicted_winner), str(correct)),
        )


def ensure_predictions(required_predictions, db_path=DEFAULT_DB_PATH):
    existing = load_predictions(db_path)
    for player, match_id, predicted_winner in required_predictions:
        stored = existing[
            (existing["Player"] == str(player))
            & (existing["Match ID"] == int(match_id))
        ]
        if len(stored) == 0 or stored.iloc[0]["Predicted Winner"] != str(predicted_winner):
            save_prediction(player, match_id, predicted_winner, db_path=db_path)


def _save_predictions_once(df, db_path=DEFAULT_DB_PATH):
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM predictions")
        for _, row in df.fillna("").iterrows():
            conn.execute(
                """
                INSERT INTO predictions (player, match_id, predicted_winner, correct, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    str(row["Player"]),
                    int(row["Match ID"]),
                    str(row["Predicted Winner"]),
                    str(row.get("Correct", "")),
                ),
            )


def save_predictions(df, db_path=DEFAULT_DB_PATH):
    attempts = 2 if _turso_config_for(db_path) is not None else 1
    last_error = None
    for _ in range(attempts):
        try:
            _save_predictions_once(df, db_path=db_path)
            return
        except Exception as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
