import sqlite3
from pathlib import Path

import pandas as pd


PREDICTION_COLUMNS = ["Player", "Match ID", "Predicted Winner", "Correct"]
DEFAULT_DB_PATH = Path("predictions.sqlite3")


def _connect(db_path=DEFAULT_DB_PATH):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
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
    return conn


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


def save_predictions(df, db_path=DEFAULT_DB_PATH):
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
