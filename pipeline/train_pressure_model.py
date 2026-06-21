"""
pipeline/train_pressure_model.py

Two models, deliberately simple given real sample sizes:

MODEL A (penalty pressure): logistic regression predicting P(goal) for a
penalty kick from shootout/sudden-death/stage context. n=202 real kicks
pooled from 2022 WC + 2018 WC + Women's WC 2023 (StatsBomb open data).
Logistic regression, not XGBoost — n=202 binary outcomes does not support
a high-capacity model without real overfitting risk, and that restraint
is itself defensible in the README.

MODEL B (late-shot residual): predicts the residual between actual outcome
and StatsBomb's baseline xG for shots in the last 15 minutes of regulation
or in extra time (n=1228), isolating a "pressure effect" on top of a shot's
intrinsic difficulty — same isolate-the-effect logic as comparing a model's
prediction against itself under different conditions, applied here to
real vs expected-goals rather than two simulated conditions.

Run this AFTER pipeline/features.py.
"""

import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

np.random.seed(42)


def bootstrap_ci(values, n_boot=5000, ci=0.95):
    boots = [np.mean(np.random.choice(values, size=len(values), replace=True)) for _ in range(n_boot)]
    lo, hi = np.percentile(boots, [(1 - ci) / 2 * 100, (1 + ci) / 2 * 100])
    return float(lo), float(hi)


def train_model_a(pen: pd.DataFrame) -> dict:
    features = ["is_shootout", "is_sudden_death", "is_knockout", "stage_weight"]
    X = pen[features].values
    y = pen["is_goal"].values

    # 5-fold CV since n=202 is too small for a held-out test split to be stable
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = LogisticRegression(max_iter=1000)
    probs = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]

    auc = roc_auc_score(y, probs)
    brier = brier_score_loss(y, probs)
    ll = log_loss(y, probs)

    # fit final model on all data for coefficient inspection / deployment
    model.fit(X, y)
    coefs = dict(zip(features, model.coef_[0].round(3).tolist()))

    overall_rate = y.mean()
    shootout_rate = pen.loc[pen.is_shootout == 1, "is_goal"].mean()
    ingame_rate = pen.loc[pen.is_shootout == 0, "is_goal"].mean()
    sd_rate = pen.loc[pen.is_sudden_death == 1, "is_goal"].mean() if pen.is_sudden_death.sum() > 0 else None

    shootout_ci = bootstrap_ci(pen.loc[pen.is_shootout == 1, "is_goal"].values)
    ingame_ci = bootstrap_ci(pen.loc[pen.is_shootout == 0, "is_goal"].values)

    return {
        "model": "logistic_regression",
        "n": int(len(pen)),
        "cv_auc": round(float(auc), 4),
        "cv_brier_score": round(float(brier), 4),
        "cv_log_loss": round(float(ll), 4),
        "coefficients": coefs,
        "overall_conversion": round(float(overall_rate), 4),
        "shootout_conversion": round(float(shootout_rate), 4),
        "shootout_conversion_95ci": [round(c, 4) for c in shootout_ci],
        "ingame_conversion": round(float(ingame_rate), 4),
        "ingame_conversion_95ci": [round(c, 4) for c in ingame_ci],
        "sudden_death_conversion": round(float(sd_rate), 4) if sd_rate is not None else None,
        "sudden_death_n": int(pen.is_sudden_death.sum()),
    }


def train_model_b(late: pd.DataFrame) -> dict:
    features = ["xg", "is_knockout", "is_extra_time", "stage_weight", "minutes_remaining"]
    X = late[features].values
    y = late["is_goal"].values

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = LogisticRegression(max_iter=1000)
    probs = cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]

    auc = roc_auc_score(y, probs)
    brier = brier_score_loss(y, probs)

    # baseline: how good is xG ALONE at predicting these same outcomes?
    baseline_auc = roc_auc_score(y, late["xg"].values)
    baseline_brier = brier_score_loss(y, late["xg"].values)

    model.fit(X, y)
    coefs = dict(zip(features, model.coef_[0].round(3).tolist()))

    sum_xg = late["xg"].sum()
    actual_goals = int(y.sum())
    knockout_residual = late.loc[late.is_knockout == 1, "xg_residual"].mean()
    group_residual = late.loc[late.is_knockout == 0, "xg_residual"].mean()

    return {
        "model": "logistic_regression_with_xg",
        "n": int(len(late)),
        "cv_auc": round(float(auc), 4),
        "cv_brier_score": round(float(brier), 4),
        "baseline_xg_only_auc": round(float(baseline_auc), 4),
        "baseline_xg_only_brier": round(float(baseline_brier), 4),
        "coefficients": coefs,
        "sum_expected_goals": round(float(sum_xg), 2),
        "actual_goals": actual_goals,
        "knockout_residual": round(float(knockout_residual), 4),
        "group_stage_residual": round(float(group_residual), 4),
    }


if __name__ == "__main__":
    pen = pd.read_parquet("data/processed/penalty_features.parquet")
    late = pd.read_parquet("data/processed/late_shot_features.parquet")

    result_a = train_model_a(pen)
    result_b = train_model_b(late)

    metrics = {"model_a_penalty_pressure": result_a, "model_b_late_shot_residual": result_b}

    with open("pipeline/model_artifacts/metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    print(json.dumps(metrics, indent=2))
