# Quarterfinal-Only Bracket Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Bracket page begin with the four confirmed quarterfinals and advance only through semifinals, third place, and final.

**Architecture:** Replace the Bracket tab's Round of 32/16 reconstruction with an explicit four-row quarterfinal dataframe. Reuse `render_round`, `advance_round`, and the existing bracket store so only quarterfinal-or-later bracket selections are persisted; do not change any prediction-page code or prediction-storage behavior.

**Tech Stack:** Python, Pandas, Streamlit, Pytest.

## Global Constraints

- Do not modify prediction-page rendering, prediction match catalog code, or prediction storage.
- Do not delete legacy Round of 32 or Round of 16 `bracket_picks` records.
- The Bracket page must show France vs Morocco, Spain vs Belgium, Norway vs England, and Argentina vs Switzerland.
- Semifinal, third-place, and final slots must be visible before their upstream winners are selected.
- Use the verified backup at `backups/20260710-bracket-qf-only/` for recovery if needed.

---

### Task 1: Replace the Bracket Entry Round

**Files:**
- Modify: `tests/test_app_static.py`
- Modify: `app.py:1095-1284`

**Interfaces:**
- Consumes: `render_round(df, title, key, interactive=True)`, `advance_round(prev_round_df)`, `restore_bracket_round(expected_round, saved_bracket)`, `save_bracket_round(round_df)`.
- Produces: a bracket flow beginning with `expected_qf`, followed by `sf_source`, `third_place`, and `final`.

- [ ] **Step 1: Write the failing test**

```python
def test_bracket_page_starts_with_confirmed_quarterfinals_only():
    assert '"Team A": "France", "Team B": "Morocco"' in SOURCE
    assert '"Team A": "Spain", "Team B": "Belgium"' in SOURCE
    assert '"Team A": "Norway", "Team B": "England"' in SOURCE
    assert '"Team A": "Argentina", "Team B": "Switzerland"' in SOURCE
    assert 'render_round(qf, "🏅 QUARTERFINALS", "qf", interactive=True)' in SOURCE
    assert '"🥊 ROUND OF 32"' not in SOURCE
    assert '"⚔️ ROUND OF 16"' not in SOURCE


def test_bracket_page_keeps_later_rounds_ready_without_touching_predictions():
    assert 'render_round(advance_round(qf), "🔥 SEMIFINALS", "sf_preview", interactive=False)' in SOURCE
    assert 'render_round(advance_round(sf_source), "🏆 FINAL", "final_preview", interactive=False)' in SOURCE
    assert 'visible_prediction_match_catalog = prediction_match_catalog[prediction_match_catalog["Group"] == "QF"].copy()' in SOURCE
```

- [ ] **Step 2: Run test to verify it fails**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_app_static.py::test_bracket_page_starts_with_confirmed_quarterfinals_only tests/test_app_static.py::test_bracket_page_keeps_later_rounds_ready_without_touching_predictions -q`

Expected: FAIL because the current tab still renders Round of 32 and Round of 16.

- [ ] **Step 3: Write the minimal implementation**

Replace the `qualifiers` gate and the Round of 32/16 blocks in `with tab3:` with an explicit quarterfinal round, then retain the existing later-round progression:

```python
expected_qf = pd.DataFrame([
    {"Match": "QF-1", "Team A": "France", "Team B": "Morocco", "Status": "Upcoming", "Winner": ""},
    {"Match": "QF-2", "Team A": "Spain", "Team B": "Belgium", "Status": "Upcoming", "Winner": ""},
    {"Match": "QF-3", "Team A": "Norway", "Team B": "England", "Status": "Upcoming", "Winner": ""},
    {"Match": "QF-4", "Team A": "Argentina", "Team B": "Switzerland", "Status": "Upcoming", "Winner": ""},
])
saved_bracket = load_bracket()
qf = restore_bracket_round(expected_qf, saved_bracket)
qf = render_round(qf, "🏅 QUARTERFINALS", "qf", interactive=True)
save_bracket_round(qf)

qf_complete = qf["Winner"].ne("").all()
if qf_complete:
    sf = restore_bracket_round(advance_round(qf), saved_bracket)
    sf = render_round(sf, "🔥 SEMIFINALS", "sf", interactive=True)
    save_bracket_round(sf)
    sf_source = sf
else:
    sf_source = advance_round(qf)
    render_round(sf_source, "🔥 SEMIFINALS", "sf_preview", interactive=False)
    st.caption("Complete all Quarterfinal winners to populate the Semifinals.")
```

Keep the existing third-place and final rendering, using `sf_source`, and remove the `r32_`/`r16_` key prefixes from the reset cleanup tuple.

- [ ] **Step 4: Run tests to verify they pass**

Run: `PYTHONPATH=. .venv/bin/pytest tests/test_app_static.py -q`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app_static.py
git commit -m "Show quarterfinal-only bracket"
```

### Task 2: Verify The Isolated Change

**Files:**
- Verify: `app.py`
- Verify: `tests/test_app_static.py`
- Verify: `tests/`

**Interfaces:**
- Consumes: the completed quarterfinal-only bracket flow from Task 1.
- Produces: evidence that bracket changes did not regress prediction behavior.

- [ ] **Step 1: Compile the modified modules**

Run: `PYTHONPATH=. .venv/bin/python -m py_compile app.py bracket_store.py prediction_matches.py`

Expected: command exits successfully with no output.

- [ ] **Step 2: Run the complete test suite**

Run: `PYTHONPATH=. .venv/bin/pytest tests -q`

Expected: all tests pass.

- [ ] **Step 3: Start the app and inspect the Bracket tab**

Run: `PYTHONPATH=. .venv/bin/python -m streamlit run app.py --server.port 8504 --server.headless true`

Expected: the Bracket tab contains only the four quarterfinals and later-stage previews; the Predictions tab remains quarterfinal-only.

- [ ] **Step 4: Commit verification-related updates only if a test assertion changed**

```bash
git add tests/test_app_static.py
git commit -m "Cover quarterfinal-only bracket"
```
