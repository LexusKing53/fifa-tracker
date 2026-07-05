from contextlib import contextmanager
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


def test_connect_preserves_original_error_when_rollback_fails(monkeypatch):
    class FakeConnection:
        def execute(self, *_args, **_kwargs):
            return None

        def rollback(self):
            raise ValueError("rollback failed")

        def close(self):
            return None

    monkeypatch.setattr(
        prediction_store,
        "_open_connection",
        lambda db_path=prediction_store.DEFAULT_DB_PATH: FakeConnection(),
    )

    try:
        with prediction_store._connect():
            raise RuntimeError("boom")
    except Exception as exc:
        assert type(exc) is RuntimeError
        assert str(exc) == "boom"
    else:
        raise AssertionError("expected RuntimeError to be raised")


def test_save_predictions_retries_once_for_turso_bulk_write(monkeypatch):
    attempts = []
    executed = []

    class FakeConnection:
        def execute(self, sql, params=None):
            executed.append((sql.strip(), params))
            return None

    @contextmanager
    def flaky_connect(db_path=prediction_store.DEFAULT_DB_PATH):
        attempts.append(str(db_path))
        if len(attempts) == 1:
            raise ValueError("Hrana: api error: status=404 Not found")
        yield FakeConnection()

    monkeypatch.setattr(prediction_store, "_connect", flaky_connect)
    monkeypatch.setattr(
        prediction_store,
        "_turso_config_for",
        lambda db_path: {"database": "libsql://fifa-tracker.turso.io", "auth_token": "token"},
    )

    prediction_store.save_predictions(
        pd.DataFrame(
            [
                {
                    "Player": "Ralph",
                    "Match ID": 7,
                    "Predicted Winner": "Brazil",
                    "Correct": "",
                }
            ]
        )
    )

    assert len(attempts) == 2
    assert executed[0][0] == "DELETE FROM predictions"
