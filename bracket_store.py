import sqlite3
from pathlib import Path

import pandas as pd


BRACKET_COLUMNS = ["Match", "Team A", "Team B", "Status", "Winner"]
DEFAULT_DB_PATH = Path("predictions.sqlite3")


def _connect(db_path=DEFAULT_DB_PATH):
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bracket_picks (
            match TEXT NOT NULL PRIMARY KEY,
            team_a TEXT NOT NULL,
            team_b TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '',
            winner TEXT NOT NULL DEFAULT '',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    return conn


def load_bracket(db_path=DEFAULT_DB_PATH):
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT match, team_a, team_b, status, winner
            FROM bracket_picks
            ORDER BY match
            """
        ).fetchall()

    return pd.DataFrame(rows, columns=BRACKET_COLUMNS)


def save_bracket_round(round_df, db_path=DEFAULT_DB_PATH):
    if len(round_df) == 0:
        return

    with _connect(db_path) as conn:
        for _, row in round_df.fillna("").iterrows():
            conn.execute(
                """
                INSERT INTO bracket_picks (match, team_a, team_b, status, winner, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(match) DO UPDATE SET
                    team_a = excluded.team_a,
                    team_b = excluded.team_b,
                    status = excluded.status,
                    winner = excluded.winner,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    str(row["Match"]),
                    str(row["Team A"]),
                    str(row["Team B"]),
                    str(row.get("Status", "")),
                    str(row.get("Winner", "")),
                ),
            )


def clear_bracket(db_path=DEFAULT_DB_PATH):
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM bracket_picks")


def restore_bracket_round(expected_round, saved_bracket):
    restored = expected_round.copy()
    if len(restored) == 0 or len(saved_bracket) == 0:
        return restored

    saved_by_match = saved_bracket.drop_duplicates(subset=["Match"]).set_index("Match")
    for idx, row in restored.iterrows():
        match_key = row["Match"]
        if match_key not in saved_by_match.index:
            continue

        saved_row = saved_by_match.loc[match_key]
        if str(saved_row["Team A"]) != str(row["Team A"]) or str(saved_row["Team B"]) != str(row["Team B"]):
            continue

        winner = str(saved_row["Winner"]).strip()
        if winner in {str(row["Team A"]), str(row["Team B"])}:
            restored.at[idx, "Winner"] = winner

    return restored
