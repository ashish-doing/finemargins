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
import streamlit.components.v1 as components

components.html("""
<style>
.fm{position:relative;width:100%;height:320px;overflow:hidden;background:#0a0a0a;border-radius:10px;font-family:sans-serif;box-sizing:border-box}
.pb{position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0px,transparent 59px,rgba(255,255,255,.03) 59px,rgba(255,255,255,.03) 60px),repeating-linear-gradient(0deg,transparent 0px,transparent 79px,rgba(255,255,255,.03) 79px,rgba(255,255,255,.03) 80px),linear-gradient(160deg,#0e1f0e 0%,#0a150a 40%,#050d05 100%)}
.pl{position:absolute;inset:0}.pl svg{width:100%;height:100%;opacity:.13}
.co{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:10;padding:0 24px;text-align:center;margin-top:-30px}
.su{margin-top:28px!important}
.ti{font-size:48px;font-weight:700;letter-spacing:-1px;color:#fff;margin:0 0 4px;line-height:1}
.ti span{color:#0f62fe}
.su{font-size:15px;color:rgba(255,255,255,.55);margin:10px 0 0;max-width:420px;line-height:1.5}
.ba{display:inline-block;margin-bottom:14px;padding:4px 12px;border:1px solid rgba(15,98,254,.45);border-radius:20px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:rgba(15,98,254,.9);background:rgba(15,98,254,.08)}
.bl{position:absolute;width:18px;height:18px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fff 0%,#ccc 60%,#999 100%);box-shadow:0 0 6px rgba(15,98,254,.6);z-index:5;animation:bm 6s cubic-bezier(.4,0,.6,1) infinite;top:54%}
@keyframes bm{0%{left:-30px;top:72%;opacity:0}5%{opacity:1}30%{left:38%;top:66%}55%{left:62%;top:62%}85%{left:100%;top:58%;opacity:1}86%{opacity:0}100%{left:100%;top:58%;opacity:0}}
.pa{position:absolute;z-index:4;opacity:.45}
.pl2{left:26%;top:55%;animation:pla 6s ease-in-out infinite}
.pr{left:66%;top:48%;animation:plb 6s ease-in-out infinite}
@keyframes pla{0%,100%{transform:translateX(0)}30%{transform:translateX(12px)}60%{transform:translateX(-4px)}}
@keyframes plb{0%,100%{transform:translateX(0) scaleX(-1)}30%{transform:translateX(-8px) scaleX(-1)}60%{transform:translateX(6px) scaleX(-1)}}
.sc{position:absolute;top:0;left:-100%;width:40%;height:100%;background:linear-gradient(90deg,transparent,rgba(15,98,254,.04),transparent);animation:sc 8s linear infinite;z-index:2}
@keyframes sc{0%{left:-40%}100%{left:140%}}
.cd{position:absolute;width:5px;height:5px;border-radius:50%;background:#0f62fe;opacity:.5}
</style>
<div class="fm">
  <div class="pb"></div>
  <div class="pl">
    <svg viewBox="0 0 800 320" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg">
      <rect x="60" y="30" width="680" height="260" fill="none" stroke="white" stroke-width="1.5"/>
      <line x1="400" y1="30" x2="400" y2="290" stroke="white" stroke-width="1.5"/>
      <circle cx="400" cy="160" r="60" fill="none" stroke="white" stroke-width="1.5"/>
      <circle cx="400" cy="160" r="3" fill="white"/>
      <rect x="60" y="100" width="90" height="120" fill="none" stroke="white" stroke-width="1.5"/>
      <rect x="650" y="100" width="90" height="120" fill="none" stroke="white" stroke-width="1.5"/>
      <rect x="60" y="115" width="30" height="90" fill="none" stroke="white" stroke-width="2"/>
      <rect x="710" y="115" width="30" height="90" fill="none" stroke="white" stroke-width="2"/>
      <path d="M150 100 A40 40 0 0 1 150 220" fill="none" stroke="white" stroke-width="1.5"/>
      <path d="M650 100 A40 40 0 0 0 650 220" fill="none" stroke="white" stroke-width="1.5"/>
      <circle cx="200" cy="160" r="2" fill="white"/>
      <circle cx="600" cy="160" r="2" fill="white"/>
    </svg>
  </div>
  <div class="sc"></div>
  <div class="pa pl2">
    <svg width="22" height="42" viewBox="0 0 22 42" xmlns="http://www.w3.org/2000/svg" fill="rgba(255,255,255,0.8)">
      <circle cx="11" cy="6" r="5"/>
      <path d="M5 13C5 11 8 10 11 10C14 10 17 11 17 13L18 26H14L13 20L11 22L9 20L8 26H4Z"/>
      <path d="M8 26L6 38H9L11 30L13 38H16L14 26Z"/>
    </svg>
  </div>
  <div class="pa pr">
    <svg width="22" height="42" viewBox="0 0 22 42" xmlns="http://www.w3.org/2000/svg" fill="rgba(255,255,255,0.65)">
      <circle cx="11" cy="6" r="5"/>
      <path d="M5 13C5 11 8 10 11 10C14 10 17 11 17 13L18 26H14L13 20L11 22L9 20L8 26H4Z"/>
      <path d="M8 26L6 38H9L11 30L13 38H16L14 26Z"/>
    </svg>
  </div>
  <div class="bl"></div>
  <div class="co">
    <div class="ba">World Cup · Pressure Intelligence</div>
    <div class="ti">Fine<span>Margins</span></div>
    <div class="su">Quantifying the pressure that decides knockout football — powered by StatsBomb open data and IBM Granite.</div>
  </div>
  <div class="cd" style="top:18px;left:18px"></div>
  <div class="cd" style="top:18px;right:18px"></div>
  <div class="cd" style="bottom:18px;left:18px"></div>
  <div class="cd" style="bottom:18px;right:18px"></div>
</div>
""", height=330)

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
