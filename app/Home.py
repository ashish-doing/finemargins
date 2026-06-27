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
st.html("""
<style>
.fm{position:relative;width:100%;height:340px;overflow:hidden;background:#0a0a0a;border-radius:10px;font-family:sans-serif;box-sizing:border-box}
.pb{position:absolute;inset:0;background:repeating-linear-gradient(90deg,transparent 0px,transparent 59px,rgba(255,255,255,.03) 59px,rgba(255,255,255,.03) 60px),repeating-linear-gradient(0deg,transparent 0px,transparent 79px,rgba(255,255,255,.03) 79px,rgba(255,255,255,.03) 80px),linear-gradient(160deg,#0e1f0e 0%,#0a150a 40%,#050d05 100%)}
.pl{position:absolute;inset:0}.pl svg{width:100%;height:100%;opacity:.13}
.co{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:10;padding:0 24px;text-align:center;margin-top:20px}
.ti{font-size:48px;font-weight:700;letter-spacing:-1px;color:#fff;margin:0 0 4px;line-height:1}
.ti span{color:#0f62fe}
.su{font-size:12px;color:rgba(255,255,255,.5);margin:12px auto 0;max-width:900px;line-height:1.6;text-align:center;white-space:nowrap}
.ba{display:inline-block;margin-bottom:14px;padding:4px 12px;border:1px solid rgba(15,98,254,.45);border-radius:20px;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:rgba(15,98,254,.9);background:rgba(15,98,254,.08)}
.bl{position:absolute;width:18px;height:18px;border-radius:50%;background:radial-gradient(circle at 35% 35%,#fff 0%,#ccc 60%,#999 100%);box-shadow:0 0 6px rgba(15,98,254,.6);z-index:5;animation:bm 6s cubic-bezier(.4,0,.6,1) infinite}
@keyframes bm{0%{left:-30px;top:88%;opacity:0}5%{opacity:1}30%{left:38%;top:82%}55%{left:62%;top:80%}85%{left:100%;top:78%;opacity:1}86%{opacity:0}100%{left:100%;top:78%;opacity:0}}
.pa{position:absolute;z-index:4;opacity:.45}
.pl2{left:26%;top:68%;animation:pla 6s ease-in-out infinite}
.pr{left:66%;top:62%;animation:plb 6s ease-in-out infinite}
.gp{position:absolute;z-index:3;opacity:.35}
.gp-l{left:0;top:30%;height:40%;width:28px;border-right:2px solid white;border-top:2px solid white;border-bottom:2px solid white}
.gp-r{right:0;top:30%;height:40%;width:28px;border-left:2px solid white;border-top:2px solid white;border-bottom:2px solid white}
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
  <div class="gp gp-l"></div>
  <div class="gp gp-r"></div>
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
""")

# ── 2026 World Cup Live Banner ────────────────────────────────────────────────
from datetime import date
_today = date.today()
if _today <= date(2026, 6, 27):
    _phase = "Group stage underway — final matchdays June 26–27."
elif _today <= date(2026, 7, 4):
    _phase = "Round of 32 underway."
elif _today <= date(2026, 7, 11):
    _phase = "Quarter-finals underway."
elif _today <= date(2026, 7, 15):
    _phase = "Semi-finals underway."
elif _today <= date(2026, 7, 19):
    _phase = "Final on July 19."
else:
    _phase = "Tournament complete — full historical record now available."

st.info(
    f"🏆 **The 2026 FIFA World Cup** — hosted across the USA, Canada & Mexico. "
    f"{_phase} Use the lenses below to benchmark live moments against real historical pressure patterns."
)

# ── Live KPIs ─────────────────────────────────────────────────────────────────
pen = load_penalties()
late = load_late_shots()
profiles = load_player_profiles()
metrics = load_metrics()

m_a = metrics["model_a_penalty_pressure"]
m_b = metrics["model_b_late_shot_residual"]

c1, c2, c3, c4, c5, c6 = st.columns([1, 1, 1, 1, 1, 1])
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

how_to_col, btn_col = st.columns([6, 1])
with how_to_col:
    st.markdown("""
    <div style="background:#0f2040;border:1px solid #0f62fe55;border-radius:8px;
                padding:0.7rem 1.4rem;display:flex;align-items:center;gap:10px">
      <span style="color:#a8c8ff;font-size:0.9rem">
        📖 <b>New to FineMargins?</b> — Learn what each page does and how to read the outputs.
      </span>
    </div>
    """, unsafe_allow_html=True)
with btn_col:
    if st.button("How to use ↓", type="primary", use_container_width=True):
        st.session_state["expand_how_to"] = True

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
    st.page_link("pages/1_Pressure_Lens.py", label="Pressure Lens — penalties & late shots", icon="⚡")
    st.page_link("pages/2_Player_Profile.py", label="Player Profiles — 159 players profiled", icon="👤")
    st.page_link("pages/3_Officiating_Lens.py", label="Officiating Lens — VAR & Laws explained", icon="🟨")
    st.page_link("pages/4_Granite_Chat.py", label="Ask Granite — IBM AI narration", icon="💬")
    st.page_link("pages/5_Tournament_Intel.py", label="Tournament Intel — analyst dashboard", icon="📊")
    st.page_link("pages/6_Methodology.py", label="Methodology — why every pipeline decision was made", icon="🔬")

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

# ── User Guide ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📖 How to use FineMargins")

st.caption("New here? Expand any section below to understand what each page does and how to read its outputs. Or jump directly to the Methodology page using the button below.")
st.page_link("pages/6_Methodology.py", label="Jump to Methodology page →", icon="🔬")
st.markdown("<br>", unsafe_allow_html=True)

_expand = st.session_state.get("expand_how_to", False)
if _expand:
    st.session_state["expand_how_to"] = False

with st.expander("⚡ Pressure Lens", expanded=_expand):
    st.markdown("""
**Two tabs: Penalty Pressure and Late-Game Shots.**

*Penalty Pressure* splits kicks by context — in-game vs shootout, early vs sudden-death round —
and shows how conversion rates shift under each pressure type. The bar charts are real counts
from 202 kicks; the percentage labels are not model predictions, they're observed rates.

*Late-Game Shots* plots 1,228 shots from the 75th minute onward. Each point is a real shot;
the colour encodes whether it was scored. The residual column shows how much the actual outcome
differed from StatsBomb's xG expectation — negative means the shot underperformed the model,
which is the pressure signal this app is built around.

**SHAP waterfall chart** — this shows *why* the model gave a particular shot its xG residual
score. Each bar is one feature (e.g. shot distance, match minute, knockout stage flag) pushing
the prediction up (red) or down (blue) from the baseline. The longer the bar, the more that
feature mattered for this specific shot. It's not a global ranking — it's an explanation for
one data point.

**Landmark moment explorer** — pick any match from the dropdown to isolate its late-game shots
on the scatter. Useful for reconstructing the pressure narrative of a specific game: which shots
were high-xG but missed, which were low-xG goals against the model's expectation.
""")

with st.expander("👤 Player Profile"):
    st.markdown("""
**Search by player name** using the text input — partial matches work (e.g. "Messi" finds
"Lionel Messi"). Only players with at least one penalty in the dataset appear; 159 players
are profiled across the three tournaments.

**Pressure breakdown chart** — a stacked bar showing each player's kicks split by context:
in-game vs shootout, and (where applicable) which shootout round. This lets you see at a glance
whether a player's record is built on easier in-game kicks or under genuine shootout pressure.

**Head-to-head comparison** — select two players from the dropdowns to place their full
pressure profiles side by side. The comparison is descriptive (real observed rates), not a
model prediction of who would win a hypothetical shootout. Small sample sizes are flagged
explicitly — a player with 2 penalties has a wide confidence interval no matter what the rate
shows.
""")

with st.expander("🟨 Officiating Lens"):
    st.markdown("""
**Six real scenarios** drawn from major tournament incidents (five from Qatar 2022 and one from the live 2026 WC), each one a case where the
officiating decision was either overturned by VAR, disputed at the time, or cited in
post-match analysis as a fine-margin call.

**The Law box** — each scenario shows the relevant IFAB Laws of the Game extract (Laws 9, 11,
12, or 14, parsed from the official 2025/26 PDF using IBM Docling). This is the actual rulebook
language the referee and VAR officials are applying, paraphrased to avoid verbatim reproduction.
It's there so you can read the rule alongside the incident, not just take the app's framing for it.

**"What this system cannot know"** — this section is intentional and important. VAR decisions
involve camera angles, real-time communication between officials, and judgment calls that no
data model can reconstruct. This box lists the specific unknowns for each scenario: what the
pitchside monitor showed, what the VAR official's exact frame was, whether the referee's
viewing angle matched the broadcast angle. The app shows you the data context; it explicitly
does not claim to adjudicate the call.
""")

with st.expander("💬 Granite Chat"):
    st.markdown("""
**Three modes**, selectable before you send a message:

- *Fan* — conversational, context-first. Granite explains pressure moments in terms of what
  they felt like and what the stakes were, drawing on the match data rather than generic
  football knowledge.
- *Analyst* — data-forward. Responses lead with the numbers (conversion rates, xG residuals,
  SHAP feature contributions) and interpret them. Best mode if you want to understand the
  methodology or interrogate a specific finding.
- *Referee trainee* — law-grounded. Responses anchor to the relevant IFAB Law text from
  `law_chunks.json` before interpreting the officiating angle. Useful for the Officiating
  Lens scenarios.

**"Grounded data" means** Granite is calling real tool functions (`get_pressure_profile`,
`get_law_text`, `get_overturn_rate`) that read from the actual processed parquet files and
law chunks — it is not generating statistics from its training data. When you see a number
in a Granite response, it came from the same dataset that powers the charts on the other pages.

**Live vs demo mode** — if `WATSONX_API_KEY` is not set in the environment, the page falls
back to demo mode, which shows pre-written example responses to illustrate the interface.
Live mode shows a 🟢 indicator in the sidebar; demo mode shows 🟡. The data tools run in
both modes; only the Granite narration layer differs.
""")

with st.expander("📊 Tournament Intelligence"):
    st.markdown("""
**CRM-style analyst dashboard** summarising all 192 matches across the three tournaments in one view.

**Tournament comparison** — side-by-side breakdown of 2018 WC, 2022 WC, and Women's WC 2023: 
penalty conversion, shootout vs in-game gap, and mean xG residual per shot. Tells you which 
tournament produced the most pressure-sensitive finishing.

**Player leaderboard** — all 159 players ranked by any metric you choose (conversion rate, 
total penalties, shootout kicks). Filter by minimum kicks taken to remove small-sample noise. 
The Gap column shows each player's in-game vs shootout differential directly.

**Pressure heatmap** — a stage × period grid showing mean xG residual per cell. 
Red = players underperformed their xG (pressure suppressed finishing). Blue = overperformed.
Lets you see at a glance which combinations of stage and match period produce the most pressure effect.

**Key facts table** — every verified number from the full dataset in one scannable reference, 
with source attribution for each figure.
""")

with st.expander("🔬 Methodology"):
    st.markdown("""
**The full technical reasoning behind every design decision in this pipeline.**

*Why residual analysis, not raw prediction* — Model B predicts the difference between
actual outcome and StatsBomb's baseline xG, not the raw outcome itself. This isolates the
pressure effect above shot quality. A raw prediction model conflates shot difficulty with
pressure context; the residual approach asks whether pressure explains variance *above and
beyond* what shot quality already predicts.

*Why AUC 0.518 is the correct finding, not a failure* — Pressure context features predict
individual penalty outcomes barely better than random. This is consistent with the
sports-science literature on penalty psychology: pressure shifts population-level base rates
but contains large irreducible variance at the individual level. Reporting AUC 0.518
prominently is a deliberate design decision — a system that buries a low AUC is not trustworthy.

*Why logistic regression, not XGBoost* — n=202 binary outcomes (Model A) does not support
a high-capacity model without real overfitting risk. Logistic regression with 4 features is
the appropriately-complex model for this dataset. It also enables exact SHAP attribution.

*Why SHAP LinearExplainer is exact here* — For linear models, SHAP has a closed-form solution.
The LinearExplainer computes exact Shapley values analytically — no sampling, no approximation.
Every SHAP waterfall chart in the Pressure Lens is exact attribution, not an estimate.

*Why 5-fold CV, not a train/test split* — At n=202 with class imbalance, a held-out 20% test
set gives ~40 samples with high AUC variance. Stratified 5-fold CV gives lower-variance estimates
with each observation appearing exactly once in a test fold.
""")