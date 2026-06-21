"""
tests/test_pipeline.py
----------------------
Validates the processed parquet files produced by the FineMargins pipeline.
Run from the project root:  pytest tests/test_pipeline.py -v
"""

import pathlib
import pytest
import pandas as pd

# ---------------------------------------------------------------------------
# Paths — all relative to the project root so they work on any machine
# ---------------------------------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"

PENALTY_PARQUET   = PROCESSED / "penalty_features.parquet"
PENALTY_SHAP      = PROCESSED / "penalty_shap.parquet"
SHOT_PARQUET      = PROCESSED / "late_shot_features.parquet"
PLAYER_PROFILES   = PROCESSED / "player_profiles.parquet"


# ---------------------------------------------------------------------------
# Fixtures — load once per session to keep the test suite fast
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def penalties_df():
    assert PENALTY_PARQUET.exists(), (
        f"Penalty parquet not found at {PENALTY_PARQUET}. "
        "Run the pipeline first: python pipeline/build_dataset.py"
    )
    return pd.read_parquet(PENALTY_PARQUET)


@pytest.fixture(scope="session")
def penalty_shap_df():
    assert PENALTY_SHAP.exists(), (
        f"SHAP parquet not found at {PENALTY_SHAP}. "
        "Run the pipeline first."
    )
    return pd.read_parquet(PENALTY_SHAP)


@pytest.fixture(scope="session")
def player_profiles_df():
    assert PLAYER_PROFILES.exists(), (
        f"Player profiles parquet not found at {PLAYER_PROFILES}."
    )
    return pd.read_parquet(PLAYER_PROFILES)


# ---------------------------------------------------------------------------
# Task (a): penalty dataset has exactly 202 rows
# ---------------------------------------------------------------------------

def test_penalty_row_count(penalties_df):
    """The StatsBomb open-data penalty extract must contain exactly 202 rows."""
    assert len(penalties_df) == 202, (
        f"Expected 202 penalty rows, got {len(penalties_df)}. "
        "Check that all three tournaments (2018 WC, 2022 WC, WWC 2023) are included "
        "and that no duplicate or extra rows have been introduced."
    )


# ---------------------------------------------------------------------------
# Task (b): overall penalty conversion rate is between 0.60 and 0.80
# ---------------------------------------------------------------------------

def test_penalty_conversion_rate_range(penalties_df):
    """
    Conversion rate should be in [0.60, 0.80].
    The 'outcome_goal' column must be 1 (scored) or 0 (missed/saved/off-target).
    Adjust the column name if your pipeline uses a different convention.
    """
    goal_col = None
    for candidate in ("outcome_goal", "is_goal", "scored", "goal"):
        if candidate in penalties_df.columns:
            goal_col = candidate
            break

    assert goal_col is not None, (
        f"Could not find a goal-outcome column in penalties_df. "
        f"Available columns: {list(penalties_df.columns)}"
    )

    rate = penalties_df[goal_col].mean()
    assert 0.60 <= rate <= 0.80, (
        f"Penalty conversion rate {rate:.3f} is outside the expected [0.60, 0.80] range. "
        "Verify that own-goal rows and retakes are handled correctly."
    )


# ---------------------------------------------------------------------------
# Task (c): SHAP columns exist in penalty_shap.parquet
# ---------------------------------------------------------------------------

EXPECTED_SHAP_PREFIXES = ("shap_",)   # column naming convention from the pipeline
MINIMUM_SHAP_COLUMNS = 3             # at least 3 feature SHAP values


def test_shap_columns_present(penalty_shap_df):
    """
    penalty_shap.parquet must contain SHAP-value columns.
    Accepts either:
      - columns starting with 'shap_'  (prefix convention)
      - a column named 'shap_values'   (stored as array)
    """
    shap_cols = [
        c for c in penalty_shap_df.columns
        if c.startswith("shap_") or c == "shap_values"
    ]
    assert len(shap_cols) >= MINIMUM_SHAP_COLUMNS, (
        f"Expected at least {MINIMUM_SHAP_COLUMNS} SHAP columns in penalty_shap.parquet, "
        f"found {len(shap_cols)}: {shap_cols}. "
        "Run the SHAP computation step in the pipeline and re-export."
    )


def test_shap_no_all_null_columns(penalty_shap_df):
    """No SHAP column should be entirely null — that indicates a pipeline error."""
    shap_cols = [c for c in penalty_shap_df.columns if c.startswith("shap_")]
    for col in shap_cols:
        null_rate = penalty_shap_df[col].isna().mean()
        assert null_rate < 1.0, (
            f"SHAP column '{col}' is entirely null. Check the SHAP export step."
        )


# ---------------------------------------------------------------------------
# Task (d): player_profiles.parquet has exactly 159 rows
# ---------------------------------------------------------------------------

def test_player_profiles_row_count(player_profiles_df):
    """Player profiles must contain exactly 159 rows."""
    assert len(player_profiles_df) == 159, (
        f"Expected 159 player-profile rows, got {len(player_profiles_df)}. "
        "Check that the minimum-appearances filter and deduplication logic "
        "in the profile builder match the original run."
    )


# ---------------------------------------------------------------------------
# Bonus sanity checks (non-blocking for the four required assertions above)
# ---------------------------------------------------------------------------

def test_penalty_df_has_no_duplicate_index(penalties_df):
    """Row index should be unique — duplicated rows suggest a join error."""
    assert not penalties_df.index.duplicated().any(), (
        "Duplicate index values found in penalties.parquet."
    )


def test_player_profiles_has_player_id(player_profiles_df):
    """Profiles must have some form of player identifier column."""
    id_cols = [c for c in player_profiles_df.columns if "player" in c.lower()]
    assert len(id_cols) >= 1, (
        f"No player-identifier column found. Columns: {list(player_profiles_df.columns)}"
    )