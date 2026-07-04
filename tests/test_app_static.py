import ast
import re
from pathlib import Path


APP = Path(__file__).resolve().parents[1] / "app.py"
STREAMLIT_CONFIG = Path(__file__).resolve().parents[1] / ".streamlit" / "config.toml"
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
    assert ".block-container { padding-top:0.4rem !important;" in SOURCE
    assert ".hero-shell { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:0.35rem; padding:0 0 0.35rem;" in SOURCE


def test_hero_uses_compact_trophy_sizing():
    assert ".trophy-img svg { width:clamp(110px, 14vw, 170px); height:auto; display:block; }" in SOURCE
    assert ".spin-ball { display:inline-block; animation:spin 2s linear infinite; font-size:2.5rem; line-height:1; }" in SOURCE


def test_group_fixture_metric_is_not_labeled_as_total_upcoming():
    assert 'render_metric_card(t("group_fixtures", lang), group_fixtures)' in SOURCE


def test_streamlit_width_api_uses_current_parameter():
    assert "use_container_width" not in SOURCE


def test_streamlit_toolbar_hides_developer_controls():
    config = STREAMLIT_CONFIG.read_text(encoding="utf-8")
    assert '[client]' in config
    assert 'toolbarMode = "viewer"' in config


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


def test_dashboard_metrics_are_centered():
    assert "def render_metric_card(" in SOURCE
    assert "dashboard-metric-value" in SOURCE
    assert "m1.metric(" not in SOURCE
    assert ".dashboard-metric { text-align:center;" in SOURCE


def test_standings_tables_explain_abbreviations():
    assert "STANDINGS_LEGEND_HTML" in SOURCE
    assert "<strong>P</strong> = Played" in SOURCE
    assert "<strong>GD</strong> = Goal Difference" in SOURCE
    assert 'st.markdown(STANDINGS_LEGEND_HTML, unsafe_allow_html=True)' in SOURCE


def test_read_only_tables_render_centered_html_cells():
    assert "def render_centered_table(" in SOURCE
    assert ".centered-table th, .centered-table td {" in SOURCE
    assert "text-align:center;" in SOURCE
    assert "st.dataframe(" not in SOURCE
    assert "render_centered_table(grp_df)" in SOURCE
    assert "render_centered_table(pd.DataFrame(rows), hide_index=True)" in SOURCE


def test_language_switch_does_not_trigger_auto_sync():
    assert SOURCE.index('st.radio("Language / Idioma"') < SOURCE.index("# Auto-sync scores from API")
    assert "language_changed = previous_lang is not None and previous_lang != lang" in SOURCE
    assert "if not language_changed:" in SOURCE


def test_fixture_cards_order_by_kickoff_datetime():
    assert "from fixture_utils import sort_matches_by_kickoff, today_et, todays_matches_for_display" in SOURCE
    assert "display_df = sort_matches_by_kickoff(display_df)" in SOURCE


def test_live_api_today_matches_include_schedule_fallbacks():
    assert "today = today_et()" in SOURCE
    assert "today_matches = todays_matches_for_display(" in SOURCE
    assert "normalize_team_name=normalize_team_name" in SOURCE


def test_prediction_game_orders_matches_by_kickoff_datetime():
    assert 'round_titles = {"R32": "Round of 32", "R16": "Round of 16"}' in SOURCE
    assert 'match_labels["Round Order"] = match_labels["Group"].map({"R32": 0, "R16": 1}).fillna(99)' in SOURCE
    assert 'match_labels = match_labels.sort_values(["Round Order", "Match ID"]).copy()' in SOURCE
    assert 'grid.sort_values(["Date", "Match ID"])' not in SOURCE


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
    assert 'match_labels["Kickoff"] = match_labels["Group"].map(round_titles).fillna("")' in SOURCE
    assert 'prediction_match_labels = build_prediction_match_labels(prediction_match_catalog)' in SOURCE
    assert 'prediction_match_labels[["Match ID", "Team A", "Team B", "Kickoff", "Group", "Match"]]' in SOURCE
    assert 'match_labels = build_prediction_match_labels(prediction_match_catalog)' in SOURCE


def test_prediction_shared_views_refresh_from_store():
    assert "# Refresh persisted predictions before shared views" in SOURCE
    assert (
        SOURCE.index("# Refresh persisted predictions before shared views")
        < SOURCE.index("# ── LEADERBOARD")
    )


def test_shared_prediction_views_do_not_require_player_name():
    shared_line = next(
        line for line in SOURCE.splitlines()
        if "# Refresh persisted predictions before shared views" in line
    )
    assert shared_line.startswith("    # Refresh persisted predictions before shared views")
    assert not shared_line.startswith("        # Refresh persisted predictions before shared views")


def test_legacy_required_prediction_injection_is_removed():
    assert "REQUIRED_PREDICTIONS" not in SOURCE
    assert "ensure_predictions(" not in SOURCE


def test_prediction_selectboxes_have_non_empty_accessible_labels():
    assert 'st.selectbox("", options' not in SOURCE
    assert 'pick_label = f"Pick winner for {match[\'Team A\']} vs {match[\'Team B\']}"' in SOURCE


def test_auto_sync_writes_scores_as_strings():
    assert 'updated.at[idx, "Team A Score"] = str(home_score)' in SOURCE
    assert 'updated.at[idx, "Team B Score"] = str(away_score)' in SOURCE


def test_bracket_keeps_future_rounds_visible_as_previews():
    assert "build_round_of_16_from_round_of_32" in SOURCE
    assert 'if prefix == "R32":' in SOURCE
    assert "return build_round_of_16_from_round_of_32(prev_round_df)" in SOURCE
    assert 'r16 = render_round(r16, "⚔️ ROUND OF 16", "r16", interactive=True)' in SOURCE
    assert 'render_round(advance_round(r32), "⚔️ ROUND OF 16", "r16_preview", interactive=False)' in SOURCE
    assert 'Complete all Round of 32 winners to populate the Round of 16.' in SOURCE


def test_round_of_32_uses_hardcoded_matchups():
    assert "ROUND_OF_32_PREDICTION_MATCHES" in SOURCE
    assert 'round_df = pd.DataFrame(ROUND_OF_32_PREDICTION_MATCHES).copy()' in SOURCE
    assert 'round_df["Match"] = [f"R32-{index + 1}" for index in range(len(round_df))]' in SOURCE
    assert 'pairs.append({"Match": f"R32-{i//2+1}", "Team A": q.loc[i, "Team"], "Team B": q.loc[i+1, "Team"], "Status": "Upcoming", "Winner": ""})' not in SOURCE


def test_predictions_page_has_separate_round_of_32_section():
    assert "from prediction_matches import (" in SOURCE
    assert "ROUND_OF_32_PREDICTION_MATCHES" in SOURCE
    assert "build_prediction_match_catalog" in SOURCE
    assert "build_round_of_16_from_round_of_32" in SOURCE
    assert 'prediction_match_catalog = build_prediction_match_catalog(st.session_state.matches)' in SOURCE
    assert 'st.markdown("### Round of 32 Predictions")' in SOURCE
    assert 'st.markdown("### Round of 16 Predictions")' in SOURCE
    assert 'knockout_options = [pick_placeholder, match["Team A"], match["Team B"], "Draw"]' in SOURCE


def test_prediction_views_hide_finished_group_matches_and_score_round_of_32():
    assert 'st.session_state.predictions = refresh_prediction_scores(st.session_state.predictions, prediction_match_catalog)' in SOURCE
    assert 'prediction_match_labels = build_prediction_match_labels(prediction_match_catalog)' in SOURCE
    assert 'upcoming = st.session_state.matches[st.session_state.matches["Status"] != "Finished"].copy()' not in SOURCE


def test_round_of_32_prediction_cards_can_show_final_locked_or_open():
    assert 'locked = is_match_locked(match)' in SOURCE
    assert '"🏁 Final" if finished else ("🔒 Locked" if locked else "🟢 Open")' in SOURCE
    assert 'pick_result = existing.iloc[0]["Correct"] if len(existing) > 0 else ""' in SOURCE
    assert 'result_badge = ""' in SOURCE
    assert 'if finished and already_picked and pick_result in ("✅", "❌"):' in SOURCE
    assert "if not finished and not locked:" in SOURCE


def test_bracket_page_uses_persisted_store():
    assert "import bracket_store" in SOURCE
    assert 'apply_live_match_results = getattr(bracket_store, "apply_live_match_results", lambda round_df, live_matches: round_df)' in SOURCE
    assert "saved_bracket = load_bracket()" in SOURCE
    assert "clear_bracket()" in SOURCE


def test_bracket_page_syncs_finished_round_of_32_results_before_advancing():
    assert "apply_live_match_results" in SOURCE
    assert "r32 = apply_live_match_results(r32, r32_live_matches)" in SOURCE


def test_leaderboard_only_counts_active_prediction_matches():
    assert 'active_predictions = filter_predictions_to_catalog(st.session_state.predictions, prediction_match_catalog)' in SOURCE
    assert 'lb = get_leaderboard(active_predictions)' in SOURCE
