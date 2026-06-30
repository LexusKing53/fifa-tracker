import pandas as pd


def score_predictions(predictions, matches):
    if len(predictions) == 0:
        return predictions.copy()

    scored = predictions.copy()
    if "Correct" not in scored.columns:
        scored["Correct"] = ""

    if len(matches) == 0 or "Match ID" not in matches.columns:
        scored["Correct"] = ""
        return scored

    match_lookup = matches.set_index("Match ID")[["Status", "Winner"]].to_dict("index")
    for idx, row in scored.iterrows():
        match = match_lookup.get(row["Match ID"])
        if match is None:
            scored.at[idx, "Correct"] = ""
            continue
        if match["Status"] != "Finished":
            scored.at[idx, "Correct"] = ""
            continue
        scored.at[idx, "Correct"] = "✅" if str(row["Predicted Winner"]) == str(match["Winner"]) else "❌"

    return scored


def filter_predictions_to_catalog(predictions, match_catalog):
    if len(predictions) == 0:
        return predictions.copy()
    if "Match ID" not in match_catalog.columns:
        return predictions.iloc[0:0].copy()
    match_ids = set(match_catalog["Match ID"].tolist())
    return predictions[predictions["Match ID"].isin(match_ids)].copy()


def prediction_result_for_pick(match_catalog, match_id, predicted_winner):
    if len(match_catalog) == 0 or "Match ID" not in match_catalog.columns:
        return ""

    match = match_catalog[match_catalog["Match ID"] == match_id]
    if len(match) == 0:
        return ""

    row = match.iloc[0]
    if row["Status"] != "Finished":
        return ""
    return "✅" if str(predicted_winner) == str(row["Winner"]) else "❌"
