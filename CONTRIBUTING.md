# Contributing to FineMargins

Thanks for your interest. This guide covers running the pipeline locally, adding new VAR scenarios, extending the IBM Granite narration, and contributing tests.

---

## Ways to Contribute

- **Bug reports** — open an issue with steps to reproduce and the page/feature affected
- **New VAR scenarios** — add a real, sourced incident to `ibm_layer/officiating_scenarios.json`
- **New Granite Chat contexts** — extend `PREBUILT_CONTEXTS` in `app/pages/4_Granite_Chat.py`
- **New pressure features** — extend `pipeline/features.py` with additional StatsBomb event fields
- **Tests** — expand `tests/` coverage for pipeline contracts or tool data grounding
- **Documentation** — improve inline comments, docstrings, or this file

---

## Local Setup

```bash
# 1. Clone
git clone https://github.com/ashish-doing/finemargins
cd finemargins

# 2. Install (Python 3.10 required — see version constraints in ARCHITECTURE.md)
pip install -r requirements.txt

# 3. IBM credentials (free Lite account at cloud.ibm.com)
export WATSONX_API_KEY=your_key_here
export WATSONX_PROJECT_ID=a4187848-e67a-4599-84cb-fb93d360ff95
export WATSONX_URL=https://us-south.ml.cloud.ibm.com
export WATSONX_MODEL_ID=ibm/granite-4-h-small

# 4. Run the data pipeline (~30s — fetches StatsBomb data)
python pipeline/features.py
python pipeline/train_pressure_model.py

# 5. Launch
streamlit run app/Home.py
```

**No watsonx.ai credentials?** All 7 pages work in demo mode — SHAP charts, player profiles, VAR scenarios, Methodology page all load from committed parquet files. Granite Chat shows pre-verified demo responses.

---

## Running Tests

```bash
pytest tests/ -v
# 18 passed
```

| File | Tests | Covers |
|---|---|---|
| `tests/test_pipeline.py` | 12 | Feature engineering, model output contracts, parquet schema |
| `tests/test_contracts.py` | 6 | Tool data grounding, ToolDataError on missing files |

All tests run fully offline — no watsonx.ai credentials required.

---

## Adding a New VAR Scenario

Add a new entry to `ibm_layer/officiating_scenarios.json` following this schema:

```json
{
  "scenario_id": "unique_slug",
  "title": "Short descriptive title",
  "tournament": "FIFA World Cup 2022",
  "match": "Team A vs Team B — Stage, Venue, Date",
  "minute": 67,
  "category": "penalty",
  "description": "Factual description of what happened and what VAR did.",
  "relevant_law": {
    "law_number": 12,
    "law_title": "Fouls and Misconduct",
    "excerpt": "Paraphrased law text — never verbatim reproduction.",
    "source_page": 94
  },
  "historical_overturn_rate": 0.556,
  "overturn_rate_source": "FIFA 2022 WC Technical Report — 5/9 penalty checks overturned",
  "what_the_model_does_not_know": [
    "The specific camera angle used by the VAR official",
    "Real-time audio between referee and VAR room",
    "Any factor specific to this incident not in a structured dataset"
  ]
}
```

**Rules:**
- Every scenario must be a real, documented incident — no hypotheticals presented as fact
- Source the overturn rate from an official report (FIFA Technical Report, ESPN VAR log, etc.)
- Law excerpts must be paraphrased, not verbatim — see `ibm_layer/docling_parser.py` for the convention
- For 2026 WC scenarios, set `"tournament": "FIFA World Cup 2026"` — the UI will automatically add the 🔴 LIVE badge

---

## Adding a New Granite Chat Context

In `app/pages/4_Granite_Chat.py`, add to the `PREBUILT_CONTEXTS` dict:

```python
"Your context label here": {
    "type": "pressure",  # pressure | officiating | residual | tournament
    "data": {
        # Real numbers only — pulled from metrics or parquet, never hardcoded approximations
        "key": value,
    },
    "default_q": "The default question shown to the user"
},
```

Then optionally add a demo response to `DEMO_RESPONSES`:

```python
("fan", "Your context label here"): """
Your pre-written demo response in fan mode...
""",
("analyst", "Your context label here"): """
Your pre-written demo response in analyst mode...
""",
```

---

## Project Structure

```
finemargins/
├── app/
│   ├── Home.py                    Entry point
│   ├── data_loader.py             Cached loaders for all parquet/JSON
│   └── pages/
│       ├── 1_Pressure_Lens.py
│       ├── 2_Player_Profile.py
│       ├── 3_Officiating_Lens.py
│       ├── 4_Granite_Chat.py
│       ├── 5_Tournament_Intel.py
│       └── 6_Methodology.py
├── pipeline/
│   ├── features.py                StatsBomb fetch + feature engineering
│   └── train_pressure_model.py    Model A + B, SHAP, CV
├── ibm_layer/
│   ├── granite_client.py          watsonx.ai SDK client
│   ├── docling_parser.py          IFAB Laws PDF → law_chunks.json
│   ├── tools.py                   3 MCP tools + ToolDataError
│   ├── law_chunks.json            Parsed IFAB Laws 2025/26
│   └── officiating_scenarios.json 6 VAR incidents
├── data/processed/                Committed parquet files
├── tests/                         18 tests
├── docs/index.html                GitHub Pages landing
├── Dockerfile                     Docker SDK for HF Spaces
├── requirements.txt               Version-pinned dependencies
├── ARCHITECTURE.md                Full system diagrams
└── CONTRIBUTING.md                This file
```

---

## Code Style

- **Python** — PEP 8, type hints on public functions, docstrings on module-level functions
- **Commit messages** — `type: description` (e.g. `feat: add new VAR scenario`, `fix: shootout_n real value`, `docs: update architecture diagram`)
- **No hardcoded approximations** — if a number comes from real data, read it from the parquet/JSON, don't `+ 109` it
- **ToolDataError always** — if a tool function can't find its data, raise `ToolDataError`, never return `None` or a default that Granite could silently narrate as fact

---

## PR Process

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make changes and run `pytest tests/ -v` — all 18 must pass
4. Open a PR with a clear description of what changed and why

---

## Questions

Open an issue on GitHub.