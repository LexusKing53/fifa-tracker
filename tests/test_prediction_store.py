from types import SimpleNamespace

import pandas as pd

import prediction_store
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


def test_save_prediction_persists_correct_marker(tmp_path):
    db_path = tmp_path / "predictions.sqlite3"

    save_prediction("Ralph", 1002, "Brazil", correct="✅", db_path=db_path)

    loaded = load_predictions(db_path=db_path)
    assert loaded.to_dict("records") == [
        {
            "Player": "Ralph",
            "Match ID": 1002,
            "Predicted Winner": "Brazil",
            "Correct": "✅",
        }
    ]


def test_default_store_uses_turso_when_streamlit_secrets_are_present(monkeypatch):
    calls = {}

    class FakeConnection:
        def execute(self, *_args, **_kwargs):
            return None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_connect(*, database, auth_token):
        calls["database"] = database
        calls["auth_token"] = auth_token
        return FakeConnection()

    def fail_sqlite_connect(*_args, **_kwargs):
        raise AssertionError("sqlite3.connect should not be used when Turso secrets are configured")

    monkeypatch.setattr(
        prediction_store,
        "st",
        SimpleNamespace(
            secrets={
                "TURSO_DATABASE_URL": "libsql://fifa-tracker.turso.io",
                "TURSO_AUTH_TOKEN": "top-secret-token",
            }
        ),
        raising=False,
    )
    monkeypatch.setattr(
        prediction_store,
        "libsql",
        SimpleNamespace(connect=fake_connect),
        raising=False,
    )
    monkeypatch.setattr(prediction_store.sqlite3, "connect", fail_sqlite_connect)

    with prediction_store._connect() as conn:
        assert isinstance(conn, FakeConnection)

    assert calls == {
        "database": "libsql://fifa-tracker.turso.io",
        "auth_token": "top-secret-token",
    }
