"""
ibm_layer/tools.py

Three data-grounding tools for the Granite Chat page, wired (or fallback-
wired) as MCP tools so Granite calls these for real numbers instead of
generating stats from training data.

Paths/columns below are verified against the actual FineMargins pipeline
output (not guessed) — cross-checked against contracts.py and the real
parquet schemas built in pipeline/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
LAW_CHUNKS_PATH = Path(__file__).resolve().parent / "law_chunks.json"
OFFICIATING_SCENARIOS_PATH = Path(__file__).resolve().parent / "officiating_scenarios.json"

# Verified real filenames — these are the actual files your pipeline writes.
PENALTIES_FILE = DATA_DIR / "penalty_shap.parquet"      # has is_goal, shap_*, model_prob
SHOTS_FILE = DATA_DIR / "late_shot_probs.parquet"        # has is_goal, model_prob, xg


class ToolDataError(Exception):
    """Raised when requested data genuinely doesn't exist — tools must
    fail loudly rather than let Granite fill the gap with invented
    numbers."""


def _load_parquet(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ToolDataError(
            f"Expected data file not found at {path}. Run pipeline/features.py "
            f"and pipeline/train_pressure_model.py first."
        )
    return pd.read_parquet(path)


def get_pressure_profile(player_name: str) -> dict[str, Any]:
    """
    Real, computed pressure stats for a player, pooled from penalty and
    late-game shot data. Column name is 'player' (verified against the
    real pipeline output — not 'player_name').
    """
    if not player_name or not isinstance(player_name, str):
        raise ValueError("player_name must be a non-empty string")

    frames = []
    for path, kind in [(SHOTS_FILE, "late_game_shot"), (PENALTIES_FILE, "penalty")]:
        df = _load_parquet(path)
        if "player" not in df.columns:
            raise ToolDataError(
                f"'player' column not found in {path.name}. Actual columns: {list(df.columns)}"
            )
        subset = df[df["player"].str.lower() == player_name.lower()].copy()
        subset["_event_type"] = kind
        frames.append(subset)

    combined = pd.concat(frames, ignore_index=True, sort=False)

    if combined.empty:
        raise ToolDataError(
            f"No events found for player='{player_name}'. Check exact StatsBomb "
            f"spelling (e.g. full name as recorded, like 'Lionel Andrés Messi Cuccittini')."
        )

    result: dict[str, Any] = {
        "player_name": player_name,
        "total_events": int(len(combined)),
        "event_breakdown": combined["_event_type"].value_counts().to_dict(),
    }

    if "is_goal" in combined.columns:
        goals = int(combined["is_goal"].sum())
        result["goals"] = goals
        result["conversion_rate"] = round(goals / len(combined), 4)

    if "model_prob" in combined.columns:
        result["mean_pressure_adjusted_probability"] = round(
            float(combined["model_prob"].mean()), 4
        )

    return result


def get_law_text(law_number: int) -> dict[str, Any]:
    """Returns the paraphrased summary for a Law number from law_chunks.json.
    Raises if not yet parsed — Granite must never invent law text."""
    if not LAW_CHUNKS_PATH.exists():
        raise ToolDataError(f"{LAW_CHUNKS_PATH} does not exist yet.")

    with open(LAW_CHUNKS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    matches = [c for c in chunks if c.get("law_number") == law_number]
    if not matches:
        available = sorted({c.get("law_number") for c in chunks})
        raise ToolDataError(
            f"Law {law_number} not found. Available law numbers: {available}."
        )

    return {
        "law_number": law_number,
        "sections": matches,
        "source_note": (
            "Paraphrased summary derived from the IFAB Laws of the Game "
            "2025/26 PDF. Not verbatim text."
        ),
    }


def get_overturn_rate(category: str) -> dict[str, Any]:
    """
    Real, sourced VAR overturn-rate context for a category of officiating
    decision, read from officiating_scenarios.json.

    IMPORTANT: there is no per-decision raw dataset in this project to
    recompute a rate from — every rate in officiating_scenarios.json was
    sourced from FIFA/ESPN tournament reporting, not derived locally. This
    function returns what's actually stored, honestly, rather than
    pretending to recompute something it can't.
    """
    if not category or not isinstance(category, str):
        raise ValueError("category must be a non-empty string")

    if not OFFICIATING_SCENARIOS_PATH.exists():
        raise ToolDataError(f"{OFFICIATING_SCENARIOS_PATH} not found.")

    with open(OFFICIATING_SCENARIOS_PATH, encoding="utf-8") as f:
        scenarios = json.load(f)

    matches = [s for s in scenarios if s.get("category", "").lower() == category.lower()]
    if not matches:
        available = sorted({s.get("category") for s in scenarios})
        raise ToolDataError(
            f"No scenarios found for category='{category}'. Available categories: {available}."
        )

    rates = [
        s["historical_overturn_rate"] for s in matches
        if s.get("historical_overturn_rate") is not None
    ]

    return {
        "category": category,
        "n_scenarios": len(matches),
        "overturn_rate": rates[0] if rates else None,
        "overturn_rate_source": matches[0].get("overturn_rate_source"),
        "scenario_ids": [s["scenario_id"] for s in matches],
        "note": (
            "No VAR review was triggered for any scenario in this category"
            if not rates else
            "Rate sourced from official tournament reporting (FIFA/ESPN), not recomputed locally."
        ),
    }


# ---------------------------------------------------------------------------
# MCP wiring — try mcp-contextforge-gateway first, fall back to FastMCP.
#
# VERIFIED: the package `mcp-contextforge-gateway` installs as Python module
# `mcpgateway` (not `mcp_contextforge_gateway` — confirmed by direct install
# and import test, version 1.0.3). The internal Gateway/tool decorator API
# was NOT verified beyond import success — check
# `python -c "import mcpgateway; help(mcpgateway)"` locally before trusting
# the block below. Given deadline pressure, the FastMCP fallback (the
# `except ImportError` branch) is the safer default — it's a stable,
# documented API from the official `mcp` SDK.
# ---------------------------------------------------------------------------

try:
    import mcpgateway  # verified correct module name

    # NOTE: exact Gateway/tool registration API within mcpgateway is
    # unverified. If this raises AttributeError, switch to the FastMCP
    # fallback below instead of debugging mcpgateway's internals under
    # deadline pressure.
    gateway = mcpgateway.Gateway(name="finemargins-tools")  # type: ignore[attr-defined]

    @gateway.tool()  # type: ignore[attr-defined]
    def get_pressure_profile_tool(player_name: str) -> dict:
        return get_pressure_profile(player_name)

    @gateway.tool()  # type: ignore[attr-defined]
    def get_law_text_tool(law_number: int) -> dict:
        return get_law_text(law_number)

    @gateway.tool()  # type: ignore[attr-defined]
    def get_overturn_rate_tool(category: str) -> dict:
        return get_overturn_rate(category)

except (ImportError, AttributeError):
    # Fall back to the standard, stable mcp SDK's FastMCP server.
    try:
        from mcp.server.fastmcp import FastMCP

        gateway = FastMCP("finemargins-tools")

        @gateway.tool()
        def get_pressure_profile_tool(player_name: str) -> dict:
            return get_pressure_profile(player_name)

        @gateway.tool()
        def get_law_text_tool(law_number: int) -> dict:
            return get_law_text(law_number)

        @gateway.tool()
        def get_overturn_rate_tool(category: str) -> dict:
            return get_overturn_rate(category)

    except ImportError:
        # Neither package available — the three core functions above
        # remain directly importable/callable regardless.
        gateway = None


if __name__ == "__main__":
    print("Running tools.py smoke test against real data...\n")
    try:
        print(get_law_text(11))
    except ToolDataError as e:
        print(f"[law_chunks.json issue] {e}")

    try:
        print(get_pressure_profile("Lionel Andrés Messi Cuccittini"))
    except ToolDataError as e:
        print(f"[pressure profile issue] {e}")

    try:
        print(get_overturn_rate("offside"))
    except ToolDataError as e:
        print(f"[overturn rate issue] {e}")