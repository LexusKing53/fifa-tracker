from datetime import datetime
from zoneinfo import ZoneInfo

from match_lock import is_match_locked, match_kickoff_at


EASTERN = ZoneInfo("America/New_York")


def test_same_day_match_is_open_before_eastern_kickoff():
    match = {"Date": "2026-06-11", "Time": "10:00 PM ET"}
    now = datetime(2026, 6, 11, 2, 30, tzinfo=EASTERN)

    assert is_match_locked(match, now=now) is False


def test_force_unlocked_match_stays_open_after_kickoff():
    match = {"Match ID": 1, "Date": "2026-06-11", "Time": "3:00 PM ET"}
    now = datetime(2026, 6, 11, 16, 30, tzinfo=EASTERN)

    assert is_match_locked(match, now=now) is False


def test_same_day_match_locks_at_eastern_kickoff():
    match = {"Date": "2026-06-11", "Time": "3:00 PM ET"}
    now = datetime(2026, 6, 11, 15, 0, tzinfo=EASTERN)

    assert is_match_locked(match, now=now) is True


def test_kickoff_uses_eastern_timezone():
    match = {"Date": "2026-06-11", "Time": "3:00 PM ET"}

    assert match_kickoff_at(match) == datetime(2026, 6, 11, 15, 0, tzinfo=EASTERN)
