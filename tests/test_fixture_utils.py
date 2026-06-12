import pandas as pd

from fixture_utils import sort_matches_by_kickoff, todays_matches_for_display


def _api_match(home, away, status="SCHEDULED", home_score=None, away_score=None):
    return {
        "homeTeam": {"name": home},
        "awayTeam": {"name": away},
        "status": status,
        "score": {"fullTime": {"home": home_score, "away": away_score}},
    }


def test_sort_matches_by_kickoff_uses_time_before_match_id():
    matches = pd.DataFrame([
        {"Match ID": 3, "Date": "2026-06-18", "Time": "9:00 PM ET", "Team A": "Mexico", "Team B": "South Korea"},
        {"Match ID": 7, "Date": "2026-06-12", "Time": "3:00 PM ET", "Team A": "Canada", "Team B": "Bosnia and Herzegovina"},
        {"Match ID": 19, "Date": "2026-06-12", "Time": "9:00 PM ET", "Team A": "United States", "Team B": "Paraguay"},
        {"Match ID": 4, "Date": "2026-06-18", "Time": "12:00 PM ET", "Team A": "Czechia", "Team B": "South Africa"},
        {"Match ID": 2, "Date": "2026-06-11", "Time": "10:00 PM ET", "Team A": "South Korea", "Team B": "Czechia"},
    ])

    ordered = sort_matches_by_kickoff(matches)

    assert ordered["Match ID"].tolist() == [2, 7, 19, 4, 3]


def test_todays_matches_for_display_fills_api_omissions_from_schedule():
    schedule = pd.DataFrame([
        {
            "Match ID": 2,
            "Date": "2026-06-11",
            "Time": "10:00 PM ET",
            "Team A": "South Korea",
            "Team B": "Czechia",
            "Team A Score": "2",
            "Team B Score": "1",
            "Status": "Finished",
        },
        {
            "Match ID": 7,
            "Date": "2026-06-12",
            "Time": "3:00 PM ET",
            "Team A": "Canada",
            "Team B": "Bosnia and Herzegovina",
            "Team A Score": "",
            "Team B Score": "",
            "Status": "Upcoming",
        },
        {
            "Match ID": 19,
            "Date": "2026-06-12",
            "Time": "9:00 PM ET",
            "Team A": "United States",
            "Team B": "Paraguay",
            "Team A Score": "",
            "Team B Score": "",
            "Status": "Upcoming",
        },
    ])
    api_matches = [
        _api_match("South Korea", "Czechia", "FINISHED", 2, 1),
        _api_match("Canada", "Bosnia-Herzegovina"),
    ]

    display = todays_matches_for_display(api_matches, schedule, today="2026-06-12")

    assert [match["homeTeam"]["name"] for match in display] == [
        "South Korea",
        "Canada",
        "United States",
    ]
    assert display[-1]["awayTeam"]["name"] == "Paraguay"
    assert display[-1]["status"] == "SCHEDULED"
