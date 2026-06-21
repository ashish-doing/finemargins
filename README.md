# ⚽ FineMargins — World Cup Pressure Intelligence

> "Football is decided by fine margins — millimeters on the pitch and split seconds of composure under pressure."

[![IBM Granite](https://img.shields.io/badge/IBM-Granite%20AI-0f62fe?logo=ibm)](https://watsonx.ai)
[![IBM Docling](https://img.shields.io/badge/IBM-Docling%202.103-0f62fe?logo=ibm)](https://github.com/DS4SD/docling)
[![IBM Context Forge](https://img.shields.io/badge/IBM-Context%20Forge%20MCP-0f62fe?logo=ibm)](https://ibm.github.io/mcp-context-forge/)
[![StatsBomb Open Data](https://img.shields.io/badge/Data-StatsBomb%20Open-00539a)](https://github.com/statsbomb/open-data)
[![License](https://img.shields.io/badge/License-Apache%202.0-green)](LICENSE)

---

## What it is

FineMargins is a two-lens World Cup pressure intelligence system:

**Lens 1 — Pressure:** Analyses every penalty kick and late-game shot across 192 real World Cup matches (2018 WC, 2022 WC, Women's WC 2023) to quantify how pressure context shifts conversion probability — and then is honest about what it can and cannot predict.

**Lens 2 — Officiating:** Explains real, documented VAR incidents from World Cup history using the actual IFAB Laws of the Game (parsed by IBM Docling), historical base rates from FIFA's official technical reports, and an explicit "what the system cannot know" panel per incident.

IBM Granite (via watsonx.ai) narrates both lenses in three modes: fan, analyst, and referee trainee — grounded in real numbers via IBM Context Forge MCP tools, never fabricating statistics.

---

## Judging criterion map

| Criterion | How FineMargins addresses it |
|---|---|
| **Human-centered AI** | Three distinct narration modes serve fans, performance analysts, and referee trainees. The "what we don't know" panel per incident puts honesty about AI limits at the center of every output. |
| **Explainability** | SHAP attribution for every individual penalty kick. All Granite responses grounded by Context Forge tool calls — every number in the narration traces to a real data source. |
| **Trust & Transparency** | Historical overturn rates from real FIFA technical reports shown alongside each VAR scenario. Model limitations stated explicitly (AUC 0.518 on individual prediction is reported, not hidden). |
| **Real-world impact** | Dual-market use: fan second-screen companion for the ongoing 2026 World Cup, and referee/coach training tool showing how a specific call compares to historical consistency. |
| **Effective use of IBM technology** | IBM Granite (watsonx.ai), IBM Docling (Laws of the Game PDF parsing), IBM Context Forge (MCP tool grounding), IBM Bob (development assistant). All four IBM technologies contribute substantively. |
| **Innovation** | Officiating lens has no direct equivalent in the June submission pool. Pressure residual methodology (isolating pressure effect against xG baseline) is methodologically stronger than a standalone prediction model. |

---

## Data

All data from **StatsBomb Open Data** (Apache 2.0 licence, [github.com/statsbomb/open-data](https://github.com/statsbomb/open-data)):

| Tournament | Competition ID | Season ID | Matches |
|---|---|---|---|
| 2022 FIFA World Cup | 43 | 106 | 64 |
| 2018 FIFA World Cup | 43 | 3 | 64 |
| FIFA Women's World Cup 2023 | 72 | 107 | 64 |

**Total: 192 matches, 4,878 shot events, 202 penalty kicks, 1,228 late-game shots.**

No scraping. No third-party APIs. All data fetched directly from the public StatsBomb GitHub repository via documented JSON endpoints.

---

## Real findings (not fabricated)

| Finding | Numbers | Source |
|---|---|---|
| Shootout vs in-game conversion gap | 65.0% (n=123) vs 74.7% (n=79) | StatsBomb WC data |
| Sudden-death conversion | 71.4% (n=14) — counter-intuitive | StatsBomb WC data |
| Expected goals overestimate in late game | 110.87 xG expected → 103 actual goals | StatsBomb WC data |
| Pressure context model AUC | 0.773 (late-shot model) | 5-fold CV, this dataset |
| Individual penalty prediction AUC | 0.518 — pressure context predicts individual outcomes poorly | 5-fold CV, this dataset |
| 2022 WC VAR penalty check overturn rate | 5/9 (56%) | FIFA 2022 WC Technical Report |

---

## Architecture

```
StatsBomb Open Data (JSON)
        │
        ▼
pipeline/fetch_statsbomb.py    ← 192 matches, 3 tournaments
        │
        ▼
pipeline/features.py           ← pressure index engineering
        │
        ├── Model A: Logistic Regression (n=202 penalties)
        │          SHAP LinearExplainer per kick
        │
        └── Model B: Logistic Regression + xG baseline (n=1,228 shots)
                   Residual analysis: actual vs xG-expected
                        │
                        ▼
              IBM Context Forge (MCP gateway)
              tools: get_pressure_profile, get_law_text, get_overturn_rate
                        │
                        ▼
              IBM Granite via watsonx.ai (ibm/granite-4-h-small)
              System prompts: fan | analyst | referee_trainee
                        │
                        ▼
              IBM Docling (IFAB Laws PDF → law_chunks.json)
                        │
                        ▼
              Streamlit app (4 pages)
              Home | Pressure Lens | Player Profiles | Officiating Lens | Granite Chat
```

---

## IBM Technology stack

| Technology | Version | Role |
|---|---|---|
| **IBM Granite** (watsonx.ai) | granite-4-h-small | Narration in 3 voice modes |
| **IBM Docling** | 2.103.0 | Parse IFAB Laws of the Game PDF → structured chunks |
| **IBM Context Forge MCP** | 1.0.3 | Tool grounding so Granite never fabricates numbers |
| **IBM Bob** | — | Development assistance throughout the build |

---

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/ashish-doing/finemargins
cd finemargins

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set IBM credentials (get free Lite account at cloud.ibm.com)
export WATSONX_API_KEY=your_key_here
export WATSONX_PROJECT_ID=your_project_id
export WATSONX_URL=https://us-south.ml.cloud.ibm.com
export WATSONX_MODEL_ID=ibm/granite-4-h-small

# 4. Run data pipeline (downloads StatsBomb data, ~30s)
python pipeline/features.py
python pipeline/train_pressure_model.py

# 5. Launch the app
streamlit run app/Home.py
```

**No watsonx.ai account?** The app runs fully in demo mode — all data visualisations, SHAP charts, player profiles, and officiating scenarios work without credentials. The Granite Chat page shows pre-verified demo responses.

---

## What the system honestly does not know

Pressure context shifts population-level base rates significantly. It does not reliably predict individual outcomes (AUC 0.518 on penalty prediction is the honest evidence for this). The system cannot know:

- A goalkeeper's form or tendency on the day
- A taker's mental state, run-up approach, or pre-kick routine
- Weather conditions, crowd noise, or fatigue level
- The specific camera angle and frame rate available to VAR officials in a given incident

These limits are displayed explicitly in the app — not buried in a methodology footnote.

---

## Developed with IBM Bob
This project was developed with assistance from IBM Bob (IBM's AI coding assistant) throughout the build process.

---

*Built for the IBM SkillsBuild AI Builders Challenge, June 2026 — "AI Inside the Match"*
*Data: StatsBomb Open Data (Apache 2.0). Laws: IFAB Laws of the Game 2025/26.*
