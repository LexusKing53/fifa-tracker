from datetime import datetime
from zoneinfo import ZoneInfo


ET_TZ = ZoneInfo("America/New_York")
TEAM_ALIASES = {
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "USA": "United States",
    "United States of America": "United States",
}


def today_et():
    return datetime.now(ET_TZ).strftime("%Y-%m-%d")


def _normalize(name, normalizer=None):
    if normalizer:
        return normalizer(name)
    team = str(name).strip()
    return TEAM_ALIASES.get(team, team)


def _match_key(team_a, team_b, normalizer=None):
    return tuple(sorted((_normalize(team_a, normalizer), _normalize(team_b, normalizer))))


def _score_value(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _status_for_api(status):
    if status == "Finished":
        return "FINISHED"
    if status == "Live":
        return "IN_PLAY"
    return "SCHEDULED"


def match_kickoff_datetime(match_row):
    date = str(match_row.get("Date", "")).strip()
    time = str(match_row.get("Time", "")).replace("ET", "").strip()
    if not date:
        return datetime.max
    for fmt, value in (("%Y-%m-%d %I:%M %p", f"{date} {time}"), ("%Y-%m-%d", date)):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.max


def sort_matches_by_kickoff(matches_df):
    ordered = matches_df.copy()
    ordered["_kickoff_sort"] = ordered.apply(match_kickoff_datetime, axis=1)
    return (
        ordered
        .sort_values(["_kickoff_sort", "Match ID"])
        .drop(columns=["_kickoff_sort"])
        .reset_index(drop=True)
    )


def _schedule_lookup(schedule_df, normalizer=None):
    lookup = {}
    for _, row in schedule_df.iterrows():
        key = _match_key(row.get("Team A", ""), row.get("Team B", ""), normalizer)
        current = lookup.get(key)
        kickoff = match_kickoff_datetime(row)
        if current is None or kickoff < current[0]:
            lookup[key] = (kickoff, row)
    return lookup


def _api_match_key(match, normalizer=None):
    home = match.get("homeTeam", {}).get("name", "")
    away = match.get("awayTeam", {}).get("name", "")
    return _match_key(home, away, normalizer)


def _schedule_row_to_api_match(row):
    return {
        "homeTeam": {"name": row.get("Team A", "")},
        "awayTeam": {"name": row.get("Team B", "")},
        "status": _status_for_api(row.get("Status", "")),
        "score": {
            "fullTime": {
                "home": _score_value(row.get("Team A Score")),
                "away": _score_value(row.get("Team B Score")),
            }
        },
    }


def todays_matches_for_display(api_matches, schedule_df, today=None, normalize_team_name=None):
    today = today or today_et()
    display_matches = list(api_matches)
    schedule = schedule_df.copy()
    lookup = _schedule_lookup(schedule, normalize_team_name)
    existing_keys = {_api_match_key(match, normalize_team_name) for match in display_matches}

    today_schedule = schedule[schedule["Date"].astype(str) == today]
    today_schedule = sort_matches_by_kickoff(today_schedule)
    for _, row in today_schedule.iterrows():
        key = _match_key(row.get("Team A", ""), row.get("Team B", ""), normalize_team_name)
        if key in existing_keys:
            continue
        display_matches.append(_schedule_row_to_api_match(row))
        existing_keys.add(key)

    def sort_key(match):
        schedule_entry = lookup.get(_api_match_key(match, normalize_team_name))
        return schedule_entry[0] if schedule_entry else datetime.max

    return [match for match in sorted(display_matches, key=sort_key)]
