import ast
import re
from pathlib import Path


APP = Path(__file__).resolve().parents[1] / "app.py"
SOURCE = APP.read_text(encoding="utf-8")


def _default_matches():
    tree = ast.parse(SOURCE)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "DEFAULT_MATCHES":
                    value = node.value
                    if isinstance(value, ast.Call):
                        value = value.args[0]
                    return ast.literal_eval(value)
    raise AssertionError("DEFAULT_MATCHES was not found")


def _key_players():
    tree = ast.parse(SOURCE)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "KEY_PLAYERS":
                    return ast.literal_eval(node.value)
    raise AssertionError("KEY_PLAYERS was not found")


def test_api_key_has_no_plaintext_fallback():
    assert not re.search(r'FOOTBALL_API_KEY",\s*"[0-9a-f]{32}"', SOURCE)
    assert "def get_secret(" in SOURCE
    assert 'API_KEY = get_secret("FOOTBALL_API_KEY")' in SOURCE


def test_group_f_uses_sweden_not_ukraine():
    group_f_teams = {
        match["Team A"]
        for match in _default_matches()
        if match["Group"] == "F"
    } | {
        match["Team B"]
        for match in _default_matches()
        if match["Group"] == "F"
    }

    assert group_f_teams == {"Netherlands", "Japan", "Sweden", "Tunisia"}


def test_known_fixture_venues_are_correct():
    fixtures = {
        (match["Team A"], match["Team B"]): match
        for match in _default_matches()
    }

    assert fixtures[("Belgium", "Egypt")]["Venue"] == "Seattle Stadium"


def test_key_players_only_include_tournament_teams():
    teams = {
        match["Team A"]
        for match in _default_matches()
    } | {
        match["Team B"]
        for match in _default_matches()
    }

    assert set(_key_players()).issubset(teams)


def test_header_has_mobile_layout_rules():
    assert "@media (max-width: 640px)" in SOURCE
    assert "hero-title" in SOURCE
    assert "hero-shell" in SOURCE


def test_trophy_is_centered_above_title_in_hero():
    assert ".hero-shell { display:flex; flex-direction:column; align-items:center; justify-content:center;" in SOURCE
    assert SOURCE.index("<div class='trophy-img'>") < SOURCE.index("<div class='hero-title-wrap'>")
    assert ".hero-title-wrap { display:flex; flex-direction:column; align-items:center; text-align:center;" in SOURCE


def test_hero_starts_near_top_of_page():
    assert ".block-container { padding-top:1.25rem !important;" in SOURCE
    assert ".hero-shell { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0.6rem; padding:0.1rem 0 0.75rem;" in SOURCE


def test_group_fixture_metric_is_not_labeled_as_total_upcoming():
    assert 'm3.metric(t("group_fixtures", lang), group_fixtures)' in SOURCE


def test_streamlit_width_api_uses_current_parameter():
    assert "use_container_width" not in SOURCE


def test_api_team_aliases_cover_common_name_variants():
    required_aliases = {
        '"Türkiye": "Turkey"',
        '"Côte d’Ivoire": "Ivory Coast"',
        "\"Côte d'Ivoire\": \"Ivory Coast\"",
        '"Curaçao": "Curacao"',
        '"Cabo Verde": "Cape Verde"',
        '"Korea Republic": "South Korea"',
        '"IR Iran": "Iran"',
        '"Congo DR": "DR Congo"',
        '"USA": "United States"',
    }

    for alias in required_aliases:
        assert alias in SOURCE
    assert "def normalize_team_name(" in SOURCE


def test_app_has_language_selector_and_translation_helper():
    assert "from translations import LANGUAGES, t" in SOURCE
    assert 'st.radio("Language / Idioma"' in SOURCE
    assert 'lang = LANGUAGES[language_label]' in SOURCE
    assert 't("fixtures_tab", lang)' in SOURCE


def test_fixture_cards_are_batched_for_fast_language_switching():
    assert "fixture_cards_html = []" in SOURCE
    assert 'fixture_cards_html.append(f"""' in SOURCE
    assert 'st.markdown("\\n".join(fixture_cards_html), unsafe_allow_html=True)' in SOURCE


def test_language_switch_does_not_trigger_auto_sync():
    assert SOURCE.index('st.radio("Language / Idioma"') < SOURCE.index("# Auto-sync scores from API")
    assert "language_changed = previous_lang is not None and previous_lang != lang" in SOURCE
    assert "if not language_changed:" in SOURCE


def test_prediction_game_orders_matches_by_date_then_match_id():
    assert 'upcoming = upcoming.sort_values(["Date", "Match ID"]).reset_index(drop=True)' in SOURCE


def test_match_start_times_are_loaded_for_default_schedule():
    assert "MATCH_START_TIMES_ET = {" in SOURCE
    assert '"Time"' in SOURCE
    assert '("2026-06-12", "Canada", "Bosnia and Herzegovina"): "3:00 PM ET"' in SOURCE
    assert '("2026-06-24", "Czechia", "Mexico"): "9:00 PM ET"' in SOURCE
    assert '("2026-06-27", "Croatia", "Ghana"): "5:00 PM ET"' in SOURCE
    assert 'lambda r: default_match_time(r) or r["Time"]' in SOURCE


def test_fixture_cards_show_start_time_with_soon_status():
    assert "format_match_datetime(row)" in SOURCE
    assert "Soon · {match_time}" in SOURCE


def test_prediction_views_show_start_time():
    assert "format_match_datetime(match)" in SOURCE
    assert 'my_preds["Kickoff"]' in SOURCE
    assert 'match_labels["Kickoff"]' in SOURCE
