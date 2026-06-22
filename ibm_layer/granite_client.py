"""
ibm_layer/granite_client.py

VERIFIED: ibm-watsonx-ai==1.5.13 imports cleanly and exposes exactly the
constructor signatures used below (checked directly against the
installed package, not assumed from memory).

NOT YET VERIFIED: an actual live call to watsonx.ai. That requires a
real IBM Cloud account + watsonx.ai project, and the watsonx endpoint
isn't reachable from the sandbox this scaffold was built in. Whoever
picks this up — run the __main__ block below FIRST, before writing any
other ibm_layer code, and confirm a real response comes back. If it
doesn't, stop and fix this before building tools.py on top of it.

Two narration modes per contracts.NarrationRequest: 'fan' and 'analyst'.
A third, 'referee_trainee', is used by the officiating lens.
"""

import os
from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import ModelInference

SYSTEM_PROMPTS = {
    "fan": (
        "You are explaining football moments to a casual fan watching the "
        "World Cup. Plain language, no jargon, short sentences. You are "
        "given real numbers in the data below — use only those numbers, "
        "never invent a statistic that isn't present in the provided data."
    ),
    "analyst": (
        "You are briefing a performance analyst. Use precise statistical "
        "language, name the features and their relative weight, state "
        "sample sizes, and flag when a finding is not statistically "
        "significant. Use only the numbers in the data below."
    ),
    "referee_trainee": (
        "You are coaching a referee development trainee. Cite the specific "
        "Law number and explain the officiating principle, not just the "
        "outcome. State plainly what the historical base rate does and does "
        "not tell us about this individual decision. Use only the numbers "
        "and law text in the data below."
    ),
}


def get_client() -> ModelInference:
    creds = Credentials(
        url=os.environ["WATSONX_URL"],
        api_key=os.environ["WATSONX_API_KEY"],
    )
    return ModelInference(
        model_id=os.environ.get("WATSONX_MODEL_ID", "ibm/granite-4-h-small"),
        credentials=creds,
        project_id=os.environ["WATSONX_PROJECT_ID"],
        params={"max_tokens": 400, "temperature": 0.3},
    )


def narrate(mode: str, grounded_data: dict, question: str | None = None) -> str:
    """mode must be one of SYSTEM_PROMPTS keys. grounded_data should already
    be the dict form of a PressureResult or OfficiatingScenario — never
    raw free text, so Granite has nothing to hallucinate around."""
    if mode not in SYSTEM_PROMPTS:
        raise ValueError(f"Unknown mode: {mode}")

    model = get_client()
    user_msg = f"Data:\n{grounded_data}\n\nQuestion: {question or 'Explain this.'}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPTS[mode]},
        {"role": "user", "content": user_msg},
    ]
    response = model.chat(messages=messages)
    return response["choices"][0]["message"]["content"]


if __name__ == "__main__":
    # PREFLIGHT CHECK — run this before anything else in ibm_layer/.
    # Requires WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL set as env vars.
    test_data = {
        "subject": "Test Player",
        "shootout_conversion": 0.65,
        "ingame_conversion": 0.747,
        "sample_size_shootout": 123,
        "sample_size_ingame": 79,
        "note": "95% CIs overlap — not statistically significant at this sample size",
    }
    print("Testing live Granite connection...")
    try:
        result = narrate("fan", test_data, "What does this pressure data tell us?")
        print("SUCCESS. Granite responded:")
        print(result)
    except KeyError as e:
        print(f"Missing env var: {e}. Set WATSONX_API_KEY, WATSONX_PROJECT_ID, WATSONX_URL.")
    except Exception as e:
        print(f"FAILED: {e}")
        print("Check: model_id is valid for your project, project_id has Granite access enabled.")
