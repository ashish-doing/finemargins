"""
tests/test_contracts.py
-----------------------
Verifies that every dataclass defined in contracts.py can be instantiated
without error, using field names matching the REAL contracts.py at the
project root (not inferred — checked directly).

Run from the project root:  pytest tests/test_contracts.py -v
"""

import importlib
import sys
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def contracts():
    try:
        mod = importlib.import_module("contracts")
    except ModuleNotFoundError:
        pytest.fail(
            "Could not import 'contracts'. Make sure contracts.py is at the "
            "project root and you are running pytest from that directory."
        )
    return mod


def test_shot_event_instantiates(contracts):
    obj = contracts.ShotEvent(
        match_id=3869685,
        tournament="2022 WC",
        stage="Final",
        player="Test Player",
        team="Test FC",
        period=1,
        minute=22,
        is_penalty=True,
        is_shootout=False,
        outcome="Goal",
        baseline_xg=0.76,
    )
    assert obj is not None
    assert obj.is_penalty is True


def test_pressure_features_instantiates(contracts):
    obj = contracts.PressureFeatures(
        minutes_remaining=23.0,
        score_diff=0,
        stage_weight=1.0,
        is_knockout=True,
        is_shootout=False,
        is_sudden_death=False,
        venue_neutral=True,
    )
    assert obj is not None


def test_pressure_result_instantiates(contracts):
    obj = contracts.PressureResult(
        subject="Test Player",
        sample_size=202,
        baseline_conversion=0.688,
        expected_xg_rate=0.65,
        pressure_adjusted_rate=0.795,
        pressure_delta=0.107,
        confidence_interval=(0.561, 0.732),
        shap_top_features=[("is_shootout", 0.342), ("stage_weight", 0.278)],
        percentile_vs_field=0.81,
    )
    assert obj is not None
    assert isinstance(obj.confidence_interval, tuple)
    assert isinstance(obj.shap_top_features, list)


def test_law_citation_instantiates(contracts):
    obj = contracts.LawCitation(
        law_number=11,
        law_title="Offside",
        excerpt="TODO — placeholder pending Docling extraction",
        source_page=51,
    )
    assert obj is not None


def test_officiating_scenario_instantiates(contracts):
    law = contracts.LawCitation(
        law_number=11,
        law_title="Offside",
        excerpt="TODO — placeholder",
        source_page=51,
    )
    obj = contracts.OfficiatingScenario(
        scenario_id="TEST_SCENARIO_001",
        title="Test Offside Scenario",
        tournament="FIFA World Cup Qatar 2022",
        match="Team A vs Team B — Group Stage, Test Stadium, 1 Jan 2022",
        minute=67,
        category="offside",
        description="A test scenario for contract validation purposes.",
        relevant_law=law,
        historical_overturn_rate=0.926,
        overturn_rate_source="ESPN Qatar 2022 VAR review log",
        what_the_model_does_not_know=[
            "Referee intent",
            "VAR room audio",
        ],
    )
    assert obj is not None
    assert obj.scenario_id == "TEST_SCENARIO_001"
    assert isinstance(obj.what_the_model_does_not_know, list)


def test_officiating_scenario_allows_null_overturn_rate(contracts):
    """historical_overturn_rate must accept None for non-reviewed incidents."""
    law = contracts.LawCitation(
        law_number=12, law_title="Fouls and Misconduct",
        excerpt="TODO", source_page=55,
    )
    obj = contracts.OfficiatingScenario(
        scenario_id="TEST_NO_REVIEW",
        title="No VAR review test",
        tournament="Test",
        match="Test",
        minute=1,
        category="discipline",
        description="Test",
        relevant_law=law,
        historical_overturn_rate=None,
        overturn_rate_source="No review occurred",
        what_the_model_does_not_know=["Something"],
    )
    assert obj.historical_overturn_rate is None


def test_narration_request_instantiates(contracts):
    obj = contracts.NarrationRequest(
        mode="fan",
        grounded_data={"shootout_conversion": 0.65, "ingame_conversion": 0.747},
        question="What does this tell us?",
    )
    assert obj is not None
    assert obj.mode in ("fan", "analyst", "referee_trainee")


def test_narration_request_question_is_optional(contracts):
    obj = contracts.NarrationRequest(
        mode="analyst",
        grounded_data={"n": 202},
    )
    assert obj.question is None


def test_narration_response_instantiates(contracts):
    obj = contracts.NarrationResponse(
        text="Based on the data, shootout penalties convert at a lower rate.",
        tool_calls_made=["get_pressure_profile"],
        grounded=True,
    )
    assert obj is not None
    assert isinstance(obj.text, str)
    assert isinstance(obj.tool_calls_made, list)
    assert isinstance(obj.grounded, bool)


def test_paths_dict_has_required_keys(contracts):
    """PATHS dict must define all file locations the rest of the app depends on."""
    required_keys = {
        "penalty_dataset", "late_shots_dataset", "pressure_model",
        "pressure_metrics", "officiating_scenarios", "law_chunks",
    }
    assert required_keys.issubset(contracts.PATHS.keys())


def test_required_env_vars_defined(contracts):
    assert "WATSONX_API_KEY" in contracts.REQUIRED_ENV_VARS
    assert "WATSONX_PROJECT_ID" in contracts.REQUIRED_ENV_VARS
    assert "WATSONX_URL" in contracts.REQUIRED_ENV_VARS