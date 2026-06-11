from datetime import datetime
from zoneinfo import ZoneInfo


EASTERN_TIME = ZoneInfo("America/New_York")


def _get(row, key, default=""):
    if hasattr(row, "get"):
        return row.get(key, default)
    return default


def match_kickoff_at(match_row):
    date = str(_get(match_row, "Date")).strip()
    time = str(_get(match_row, "Time")).strip().replace(" ET", "")
    if not date or not time:
        return None
    try:
        kickoff = datetime.strptime(f"{date} {time}", "%Y-%m-%d %I:%M %p")
    except ValueError:
        return None
    return kickoff.replace(tzinfo=EASTERN_TIME)


def is_match_locked(match_row, now=None):
    kickoff = match_kickoff_at(match_row)
    if kickoff is None:
        try:
            match_date = datetime.strptime(str(_get(match_row, "Date")).strip(), "%Y-%m-%d")
        except ValueError:
            return False
        today = (now or datetime.now(EASTERN_TIME)).astimezone(EASTERN_TIME).date()
        return match_date.date() <= today

    current = now or datetime.now(EASTERN_TIME)
    if current.tzinfo is None:
        current = current.replace(tzinfo=EASTERN_TIME)
    return current.astimezone(EASTERN_TIME) >= kickoff
