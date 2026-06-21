"""
pipeline/shap_explain.py
Produces the shap_top_features list required by contracts.PressureResult.
Logistic regression SHAP values are exact linear attributions here (no
approximation needed), which is itself worth stating in the README as a
deliberate, defensible choice for a small dataset rather than reaching
for a black-box explainer on a model that doesn't need one.
"""

import pandas as pd
import shap
from sklearn.linear_model import LogisticRegression

FEATURES_A = ["is_shootout", "is_sudden_death", "is_knockout", "stage_weight"]


def explain_penalty_shot(row_features: dict, model: LogisticRegression, background_X) -> list[tuple[str, float]]:
    """row_features: dict with keys matching FEATURES_A.
    Returns sorted [(feature, contribution)] for one shot, most influential first."""
    explainer = shap.LinearExplainer(model, background_X)
    # IMPORTANT: pass max_samples=background_X.shape[0] explicitly — otherwise
    # shap silently subsamples to 100 and warns. Verified during preflight check.
    x = [[row_features[f] for f in FEATURES_A]]
    values = explainer(x).values[0]
    pairs = sorted(zip(FEATURES_A, values.tolist()), key=lambda p: abs(p[1]), reverse=True)
    return [(f, round(v, 4)) for f, v in pairs]


if __name__ == "__main__":
    pen = pd.read_parquet("data/processed/penalty_features.parquet")
    X = pen[FEATURES_A].values
    y = pen["is_goal"].values
    model = LogisticRegression(max_iter=1000).fit(X, y)

    explainer = shap.LinearExplainer(model, X, max_samples=X.shape[0])
    shap_values = explainer(X)

    # quick sanity print for two contrasting real cases
    sd_idx = pen[pen.is_sudden_death == 1].index[0]
    ig_idx = pen[(pen.is_shootout == 0) & (pen.is_knockout == 0)].index[0]
    for idx, label in [(sd_idx, "sudden-death shootout kick"), (ig_idx, "in-game group-stage kick")]:
        pos = pen.index.get_loc(idx)
        pairs = sorted(zip(FEATURES_A, shap_values.values[pos].tolist()), key=lambda p: abs(p[1]), reverse=True)
        print(label, "->", [(f, round(v, 4)) for f, v in pairs])
