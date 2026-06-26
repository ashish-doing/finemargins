# FineMargins — Architecture

## Overview

FineMargins has two analytical lenses — a **Pressure Pipeline** that trains ML models on real World Cup shot data, and an **Officiating Lens** that grounds IBM Granite narration in IFAB Laws parsed by IBM Docling. Both lenses feed into a 7-page Streamlit app deployed via Docker on HuggingFace Spaces.

---

## System Diagram

```mermaid
flowchart TD
    subgraph DATA["📊 DATA LAYER"]
        SB["StatsBomb Open Data\n━━━━━━━━━━━━━━━\n192 matches · 3 tournaments\n2018 WC · 2022 WC · WWC 2023\nConcurrent fetch via ThreadPoolExecutor"]
        IFAB["IFAB Laws of the Game PDF\n━━━━━━━━━━━━━━━\n2025/26 edition\nMulti-column layout + footnotes"]
        VAR["officiating_scenarios.json\n━━━━━━━━━━━━━━━\n6 VAR incidents\n5 Qatar 2022 + 1 live 2026 WC\nSourced from FIFA/ESPN reports"]
    end

    subgraph PIPELINE["⚙️ PIPELINE LAYER"]
        FEAT["pipeline/features.py\n━━━━━━━━━━━━━━━\nPressure feature engineering\nis_shootout · is_sudden_death\nstage_weight · xg_residual"]
        TRAIN["pipeline/train_pressure_model.py\n━━━━━━━━━━━━━━━\nModel A: 202 penalties → AUC 0.518\nModel B: 1,228 shots → AUC 0.773\n5-fold CV · Bootstrap CIs · SHAP"]
        DOCLING["ibm_layer/docling_parser.py\n━━━━━━━━━━━━━━━\nIBM Docling 2.103\nPDF → law_chunks.json\nLayout-aware extraction"]
    end

    subgraph IBM["🔵 IBM LAYER"]
        TOOLS["ibm_layer/tools.py\n━━━━━━━━━━━━━━━\nContext Forge MCP server\nget_pressure_profile()\nget_law_text()\nget_overturn_rate()\nToolDataError if data absent"]
        GRANITE["ibm_layer/granite_client.py\n━━━━━━━━━━━━━━━\nIBM Granite ibm/granite-4-h-small\nvia watsonx.ai SDK 1.3.42\nModes: fan · analyst · referee_trainee"]
    end

    subgraph APP["🖥️ STREAMLIT APP (7 pages)"]
        HOME["Home.py\n━━━━━━━━━━━━━━━\nAnimated pitch hero\nLive 2026 WC banner (dynamic)\nKPI cards · Key findings"]
        P1["1_Pressure_Lens.py\n━━━━━━━━━━━━━━━\nPenalty conversion charts\nSHAP waterfall per kick\nLandmark moment explorer"]
        P2["2_Player_Profile.py\n━━━━━━━━━━━━━━━\n159 players · search\nHead-to-head comparison\nPressure breakdown chart"]
        P3["3_Officiating_Lens.py\n━━━━━━━━━━━━━━━\n6 VAR scenarios\nLaw citations (Docling)\n🔴 LIVE 2026 badge"]
        P4["4_Granite_Chat.py\n━━━━━━━━━━━━━━━\n7 prebuilt contexts\n3 narration modes\nLive Granite + demo fallback"]
        P5["5_Tournament_Intel.py\n━━━━━━━━━━━━━━━\nCRM dashboard\nPlayer leaderboard + CSV export\nPressure heatmap"]
        P6["6_Methodology.py\n━━━━━━━━━━━━━━━\n9 sections\nWhy every design decision\nwas made — explicitly"]
    end

    SB --> FEAT
    FEAT --> TRAIN
    IFAB --> DOCLING
    TRAIN -->|parquet artifacts| TOOLS
    DOCLING -->|law_chunks.json| TOOLS
    VAR -->|scenarios JSON| TOOLS
    TOOLS --> GRANITE
    GRANITE --> P4
    TRAIN --> P1
    TRAIN --> P2
    TRAIN --> P5
    DOCLING --> P3
    VAR --> P3
    HOME --- P1 --- P2 --- P3 --- P4 --- P5 --- P6
```

---

## Request Flow — Pressure Lens

```mermaid
sequenceDiagram
    participant User
    participant PL as Pressure Lens (Streamlit)
    participant DL as data_loader.py
    participant PQ as penalty_shap.parquet
    participant SH as SHAP LinearExplainer

    User->>PL: Select kick from landmark explorer
    PL->>DL: load_penalties()
    DL->>PQ: pd.read_parquet()
    PQ-->>DL: 202 rows × features
    DL-->>PL: filtered DataFrame
    PL->>SH: explainer(row_features)
    SH-->>PL: exact Shapley values (no approximation)
    PL-->>User: SHAP waterfall chart + pressure context stats
```

---

## Request Flow — Granite Chat

```mermaid
sequenceDiagram
    participant User
    participant GC as Granite Chat (Streamlit)
    participant TL as ibm_layer/tools.py
    participant PQ as parquet/JSON data
    participant GR as IBM Granite (watsonx.ai)

    User->>GC: Select context + ask question
    GC->>TL: get_pressure_profile() / get_law_text() / get_overturn_rate()
    TL->>PQ: read real parquet or JSON
    PQ-->>TL: verified numbers
    TL-->>GC: structured data dict (or ToolDataError)
    GC->>GC: Inject data as grounded context into prompt
    GC->>GR: narrate(mode, data, question) via watsonx.ai SDK
    GR-->>GC: narration grounded in real numbers
    GC-->>User: Response with 🟢 Live Granite indicator
```

---

## Request Flow — Officiating Lens

```mermaid
sequenceDiagram
    participant User
    participant OL as Officiating Lens (Streamlit)
    participant SC as officiating_scenarios.json
    participant LC as law_chunks.json

    User->>OL: Select VAR incident
    OL->>SC: load_scenarios()
    SC-->>OL: scenario with tournament, minute, category
    OL->>LC: get_law_text(law_number)
    LC-->>OL: paraphrased law excerpt + source page
    OL-->>User: Law box + overturn rate + "what cannot be known" panel
    Note over OL,User: 🔴 LIVE badge shown if tournament == "FIFA World Cup 2026"
```

---

## Pipeline — Feature Engineering

```mermaid
flowchart LR
    A["StatsBomb JSON\n192 matches"] --> B["Extract shot events\nperiod ≥ 2, minute ≥ 75\nor penalty type"]
    B --> C{"Shot type"}
    C -->|penalty| D["Model A features\n━━━━━━━━━━━━━\nis_shootout\nis_sudden_death\nis_knockout\nstage_weight"]
    C -->|late-game| E["Model B features\n━━━━━━━━━━━━━\nxg_residual = is_goal − xG\nminutes_remaining\nstage_weight\nis_extra_time"]
    D --> F["penalty_shap.parquet\nn=202"]
    E --> G["late_shot_probs.parquet\nn=1,228"]
```

---

## Model Architecture

```mermaid
flowchart TD
    subgraph A["Model A — Penalty Pressure"]
        A1["n = 202 binary outcomes\n4 features\nLogistic Regression"]
        A2["5-fold stratified CV\nAUC = 0.518\nHonest null result"]
        A3["SHAP LinearExplainer\nExact Shapley values\nNo approximation"]
        A1 --> A2 --> A3
    end

    subgraph B["Model B — Late-Shot Residual"]
        B1["n = 1,228 shots\nTarget: is_goal − xG\nLogistic Regression"]
        B2["5-fold CV\nAUC = 0.773\nBaseline xG-only = 0.807"]
        B3["Finding: pressure does not\nimprove individual discrimination\nover xG alone — correct null result"]
        B1 --> B2 --> B3
    end
```

---

## IBM Technology Layer

```mermaid
flowchart LR
    subgraph DOCLING["IBM Docling 2.103"]
        D1["IFAB Laws PDF\n2025/26 edition"]
        D2["Layout-aware extraction\nMulti-column + footnotes"]
        D3["law_chunks.json\nLaws 9 · 11 · 12 · 14"]
        D1 --> D2 --> D3
    end

    subgraph MCP["IBM Context Forge MCP 1.0.3"]
        M1["get_pressure_profile(player)\nReads penalty_shap.parquet"]
        M2["get_law_text(law_number)\nReads law_chunks.json"]
        M3["get_overturn_rate(category)\nReads officiating_scenarios.json"]
        M4["ToolDataError\nif data absent\n— no hallucination path"]
        M1 & M2 & M3 --> M4
    end

    subgraph GRANITE["IBM Granite (watsonx.ai)"]
        G1["ibm/granite-4-h-small\nvia ibm-watsonx-ai SDK 1.3.42"]
        G2["fan mode\nanalyst mode\nreferee_trainee mode"]
        G3["Receives structured data\nfrom tool layer only\nNever generates statistics freely"]
        G1 --> G2 --> G3
    end

    D3 --> M2
    M1 & M2 & M3 --> G3
```

---

## Deployment Architecture

```mermaid
flowchart TD
    subgraph LOCAL["Local Development"]
        L1["python pipeline/features.py"]
        L2["python pipeline/train_pressure_model.py"]
        L3["streamlit run app/Home.py"]
        L1 --> L2 --> L3
    end

    subgraph GIT["Git (dual remote)"]
        G1["git push origin main"]
        G2["GitHub repo\nashish-doing/finemargins"]
        G3["HuggingFace Space\nashish-doing/finemargins"]
        G1 --> G2
        G1 --> G3
    end

    subgraph HF["HuggingFace Spaces (Docker SDK)"]
        H1["Dockerfile\nPython 3.10 base"]
        H2["requirements.txt\nversion-pinned"]
        H3["4 watsonx secrets\nWATSONX_API_KEY\nWATSONX_PROJECT_ID\nWATSONX_URL\nWATSONX_MODEL_ID"]
        H4["Streamlit app\nport 7860"]
        H1 --> H2 --> H3 --> H4
    end

    subgraph PAGES["GitHub Pages"]
        P1["docs/index.html\nLanding page"]
    end

    G3 --> HF
    G2 --> PAGES
```

---

## Data Flow — Anti-Hallucination

```mermaid
flowchart LR
    A["User asks Granite\na question"] --> B["Granite Chat\nselects context type"]
    B --> C["tools.py called\nas Python function"]
    C --> D{"Data file\nexists?"}
    D -->|yes| E["Returns real dict\nfrom parquet/JSON"]
    D -->|no| F["Raises ToolDataError\n— request fails loudly"]
    E --> G["Injected as structured\nJSON into Granite prompt"]
    G --> H["Granite narrates\nonly the provided numbers"]
    F --> I["Error shown to user\nGranite not called"]
```

---

## Component Map

| File | Responsibility |
|---|---|
| `app/Home.py` | Entry point — animated pitch hero, dynamic 2026 WC banner, KPI cards, explore lenses, how-to-use guide |
| `app/data_loader.py` | Cached `@st.cache_data` loaders for all parquet/JSON artifacts |
| `app/pages/1_Pressure_Lens.py` | Penalty conversion charts, SHAP waterfall, xG residual by minute, landmark explorer |
| `app/pages/2_Player_Profile.py` | 159 player profiles, search, head-to-head comparison |
| `app/pages/3_Officiating_Lens.py` | 6 VAR scenarios, IFAB Law citations, overturn rates, 🔴 LIVE 2026 badge |
| `app/pages/4_Granite_Chat.py` | 7 prebuilt contexts, 3 narration modes, live Granite + verified demo fallback |
| `app/pages/5_Tournament_Intel.py` | Cross-tournament CRM dashboard, player leaderboard, CSV export, pressure heatmap |
| `app/pages/6_Methodology.py` | 9-section methodology — why every pipeline decision was made |
| `pipeline/features.py` | StatsBomb concurrent fetch + pressure feature engineering → parquet |
| `pipeline/train_pressure_model.py` | Model A + B training, 5-fold CV, bootstrap CIs, SHAP artifacts |
| `ibm_layer/granite_client.py` | watsonx.ai SDK client — narrate(mode, data, question) |
| `ibm_layer/docling_parser.py` | IFAB Laws PDF → law_chunks.json via IBM Docling |
| `ibm_layer/tools.py` | Context Forge MCP server — 3 grounding tools + ToolDataError |
| `ibm_layer/law_chunks.json` | Parsed IFAB Laws 2025/26 (Laws 9, 11, 12, 14) |
| `ibm_layer/officiating_scenarios.json` | 6 VAR incidents with Law citations, overturn rates, sourcing |
| `data/processed/` | Committed parquet files — no pipeline run needed to explore app |
| `tests/` | 18 tests — pipeline contracts, model output schema, tool data grounding |
| `docs/index.html` | GitHub Pages landing page |
| `Dockerfile` | Docker SDK config for HF Spaces — Python 3.10, port 7860 |

---

## Key Version Constraints

| Package | Version | Reason |
|---|---|---|
| `streamlit` | `>=1.35.0` | `st.page_link` requires 1.31+; st.html requires 1.35+ |
| `ibm-watsonx-ai` | `==1.3.42` | 1.5.13+ requires Python 3.11; API signatures identical |
| `shap` | `>=0.44.0,<0.50.0` | 0.52+ requires Python 3.12+ |
| `python` | `3.10` | HF Spaces Docker base + dependency ceiling |

---

*Built for the IBM SkillsBuild AI Builders Challenge, June 2026 — "AI Inside the Match"*