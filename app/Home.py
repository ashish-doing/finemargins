"""
app/Home.py  — FineMargins entry point

Run: streamlit run app/Home.py
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app.data_loader import load_penalties, load_player_profiles, load_metrics, load_late_shots

st.set_page_config(
    page_title="FineMargins — World Cup Pressure Intelligence",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
:root { --ibm-blue: #0f62fe; --ibm-dark: #161616; --ibm-gray: #393939; }
.hero {
    background: linear-gradient(135deg, #0f62fe 0%, #00539a 60%, #161616 100%);
    padding: 3rem 2rem 2.5rem;
    border-radius: 12px;
    margin-bottom: 2rem;
    color: white;
}
.hero h1 { font-size: 2.8rem; font-weight: 700; margin: 0; letter-spacing: -1px; }
.hero p { font-size: 1.15rem; opacity: 0.88; margin-top: 0.6rem; }
.kpi-box {
    background: #1c1c1c;
    border: 1px solid #393939;
    border-radius: 8px;
    padding: 1.2rem 1.4rem;
    text-align: center;
}
.kpi-box .val { font-size: 2.2rem; font-weight: 700; color: #0f62fe; }
.kpi-box .label { font-size: 0.82rem; color: #a8a8a8; margin-top: 0.25rem; }
.insight-card {
    background: #1c1c1c;
    border-left: 4px solid #0f62fe;
    border-radius: 6px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.tech-badge {
    display: inline-block;
    background: #0f62fe22;
    border: 1px solid #0f62fe55;
    color: #78a9ff;
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 0.78rem;
    margin: 2px;
}
</style>
""", unsafe_allow_html=True)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>⚽ FineMargins</h1>
  <p>World Cup pressure intelligence — what really happens when it matters most,<br>
  explained with real data from 192 matches across three major tournaments.</p>
</div>
""", unsafe_allow_html=True)

# ── Live KPIs ─────────────────────────────────────────────────────────────────
pen = load_penalties()
late = load_late_shots()
profiles = load_player_profiles()
metrics = load_metrics()

m_a = metrics["model_a_penalty_pressure"]
m_b = metrics["model_b_late_shot_residual"]

c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    ("192", "Matches analysed", "2018 WC · 2022 WC · WWC 2023"),
    (f"{len(pen)}", "Penalty kicks", "In-game + shootout"),
    (f"{len(late):,}", "Late-game shots", "75′ – 120′ + extra time"),
    (f"{len(profiles)}", "Player profiles", "With ≥1 penalty in data"),
    (f"{m_a['shootout_conversion']:.1%}", "Shootout conversion", f"vs {m_a['ingame_conversion']:.1%} in-game"),
    (f"{m_b['cv_auc']:.3f}", "Late-shot model AUC", "Pressure-context model"),
]
for col, (val, label, sub) in zip([c1,c2,c3,c4,c5,c6], kpis):
    with col:
        st.markdown(f"""
        <div class="kpi-box">
          <div class="val">{val}</div>
          <div class="label">{label}<br><span style="opacity:0.6;font-size:0.75rem">{sub}</span></div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Two columns: Key Findings + Navigation ──────────────────────────────────
left, right = st.columns([3, 2], gap="large")

with left:
    st.markdown("### 🔬 What the data actually shows")

    st.markdown("""<div class="insight-card">
    <b>Shootout kicks convert 9.7 percentage points less than in-game penalties.</b><br>
    65.0% (80/123) versus 74.7% (59/79) — a real, measurable effect that persists
    across all three tournaments in this dataset. 95% bootstrap CIs overlap slightly,
    so the effect is substantial but not yet at p&lt;0.05 at this sample size.
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="insight-card">
    <b>Sudden-death kicks don't collapse the way intuition says.</b><br>
    71.4% conversion rate on 14 real sudden-death kicks — higher than regular
    shootout kicks (65.0%), counter-intuitive and small-sample, but real.
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="insight-card">
    <b>World Cup expected-goals models overestimate slightly under pressure.</b><br>
    StatsBomb's xG model expected 110.87 late-game goals in this dataset; 103 were
    actually scored. Knockout rounds show a −0.71% residual per shot vs −0.61%
    in the group stage — pressure suppresses finishing slightly beyond what shot
    location alone predicts.
    </div>""", unsafe_allow_html=True)

    st.markdown("""<div class="insight-card">
    <b>An AUC of 0.518 on individual penalty prediction is an honest finding,
    not a failure.</b><br>
    Pressure context shifts population-level base rates significantly but predicts
    individual outcomes poorly — consistent with sports-science evidence that
    penalty outcomes are close to coin-flips when matched for skill level.
    </div>""", unsafe_allow_html=True)

with right:
    st.markdown("### 🗺️ Explore the lenses")
    st.page_link("pages/1_Pressure_Lens.py", label="⚡ Pressure Lens — penalties & late shots", icon="⚡")
    st.page_link("pages/2_Player_Profile.py", label="👤 Player Profiles — 159 players profiled", icon="👤")
    st.page_link("pages/3_Officiating_Lens.py", label="🟨 Officiating Lens — VAR & Laws explained", icon="🟨")
    st.page_link("pages/4_Granite_Chat.py", label="💬 Ask Granite — IBM AI narration", icon="💬")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Powered by")
    techs = ["IBM Granite (watsonx.ai)", "IBM Docling 2.103", "IBM Context Forge MCP",
             "StatsBomb Open Data", "scikit-learn", "SHAP", "Streamlit"]
    st.markdown(" ".join(f'<span class="tech-badge">{t}</span>' for t in techs), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📋 Data provenance")
    st.caption(
        "All shot events from StatsBomb's open-data repository (StatsBomb Public Data User Agreement)."
        "2022 FIFA World Cup (competition 43, season 106), "
        "2018 FIFA World Cup (competition 43, season 3), "
        "FIFA Women's World Cup 2023 (competition 72, season 107). "
        "No scraping; direct JSON from the public GitHub repo."
    )
