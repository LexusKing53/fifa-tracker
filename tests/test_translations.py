from translations import LANGUAGES, t


def test_spanish_translates_main_navigation_labels():
    assert LANGUAGES == {"English": "en", "Español": "es"}
    assert t("fixtures_tab", "es") == "📅 PARTIDOS"
    assert t("standings_tab", "es") == "📊 POSICIONES"
    assert t("predictions_tab", "es") == "🎯 PREDICCIONES"
    assert t("filter_by_group", "es") == "Filtrar por grupo"


def test_translation_falls_back_to_english_for_unknown_language():
    assert t("save_fixtures", "zz") == "💾 Save Fixtures"
