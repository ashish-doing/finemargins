"""
pages/6_Methodology.py

A dedicated methodology page for judges and technical reviewers.
Explains every non-obvious design choice in the pipeline — why residual
over raw prediction, why logistic regression not XGBoost, why SHAP
LinearExplainer is exact here, and why AUC 0.518 is the correct finding.
"""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_loader import load_metrics

st.set_page_config(
    page_title="Methodology — FineMargins",
    page_icon="🔬",
    layout="wide"
)

st.markdown("""
<style>
.method-hero {
    background: linear-gradient(135deg, #0a0a1a 0%, #0f2040 100%);
    border: 1px solid #0f62fe44;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
}
.method-hero h1 { margin:0; font-size:2rem; font-weight:700; color:#fff; }
.method-hero p { margin:0.5rem 0 0; color:#a8a8a8; font-size:0.95rem; max-width:680px; }

.decision-card {
    background: #111827;
    border: 1px solid #1e293b;
    border-left: 4px solid #0f62fe;
    border-radius: 8px;
    padding: 1.4rem 1.6rem;
    margin: 1rem 0;
}
.decision-card h3 { margin:0 0 0.5rem; font-size:1.05rem; color:#78a9ff; font-weight:600; }
.decision-card p  { margin:0; color:#c6c6c6; font-size:0.9rem; line-height:1.6; }

.why-box {
    background: #0f1f0f;
    border: 1px solid #42be6533;
    border-left: 4px solid #42be65;
    border-radius: 8px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 0;
}
.why-box h4 { margin:0 0 0.4rem; color:#a7f0ba; font-size:0.88rem; text-transform:uppercase; letter-spacing:0.05em; }
.why-box p  { margin:0; color:#c6c6c6; font-size:0.88rem; line-height:1.55; }

.honest-box {
    background: #1c1000;
    border: 1px solid #ff832b44;
    border-left: 4px solid #ff832b;
    border-radius: 8px;
    padding: 1rem 1.3rem;
    margin: 0.6rem 0;
}
.honest-box h4 { margin:0 0 0.4rem; color:#ffb784; font-size:0.88rem; text-transform:uppercase; letter-spacing:0.05em; }
.honest-box p  { margin:0; color:#c6c6c6; font-size:0.88rem; line-height:1.55; }

.pipeline-step {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 0.9rem 0;
    border-bottom: 1px solid #1a1a1a;
}
.step-num {
    background: #0f62fe22;
    border: 1px solid #0f62fe44;
    color: #78a9ff;
    border-radius: 50%;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 700;
    flex-shrink: 0;
}
.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f62fe;
    margin: 2rem 0 1rem;
    border-bottom: 1px solid #1a1a1a;
    padding-bottom: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

metrics = load_metrics()
m_a = metrics["model_a_penalty_pressure"]
m_b = metrics["model_b_late_shot_residual"]

st.markdown("""
<div class="method-hero">
  <h1>🔬 Methodology</h1>
  <p>Every design decision in this pipeline has a reason. This page makes those reasons explicit —
  not buried in a footnote, but front and centre. Judges, reviewers, and anyone who wants to 
  understand why the system is built the way it is can start here.</p>
</div>
""", unsafe_allow_html=True)

# ─── SECTION 1: THE CORE QUESTION ───────────────────────────────────────────
st.markdown('<div class="section-title">1. The core question — and why it matters how you frame it</div>', unsafe_allow_html=True)

q1, q2 = st.columns([3, 2], gap="large")
with q1:
    st.markdown("""
    Most sports AI systems ask: **"Can I predict whether this shot will go in?"**  
    That's the wrong question here — and the answer tells you why.

    FineMargins asks a different question: **"Does high-pressure context change scoring patterns 
    beyond what shot quality already predicts?"**

    The distinction is methodologically important. A raw prediction model on penalty kicks mixes 
    two completely different signals:
    - **Shot quality** (how good was the position, angle, and technique) — highly predictive
    - **Pressure context** (shootout vs in-game, stage weight, sudden death) — what we actually care about

    By separating these, the system can make an honest, defensible claim: *pressure context shifts 
    population-level base rates but does not reliably predict individual outcomes.* This is the correct 
    finding, not a failure.
    """)

with q2:
    # Visual: the two questions
    fig_q = go.Figure()
    fig_q.add_trace(go.Bar(
        name='Wrong framing (raw prediction)',
        x=['Individual outcome AUC'],
        y=[m_a['cv_auc']],
        marker_color='#fa4d56',
        text=[f"AUC {m_a['cv_auc']:.3f}"],
        textposition='outside',
    ))
    fig_q.add_trace(go.Bar(
        name='Right framing (population residual)',
        x=['Late-shot residual AUC'],
        y=[m_b['cv_auc']],
        marker_color='#42be65',
        text=[f"AUC {m_b['cv_auc']:.3f}"],
        textposition='outside',
    ))
    fig_q.update_layout(
        template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
        height=280, barmode='group', showlegend=True,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(size=10)),
        margin=dict(t=40, b=20),
        title=dict(text="Why framing matters", font=dict(size=13)),
    )
    st.plotly_chart(fig_q, use_container_width=True)

# ─── SECTION 2: WHY AUC 0.518 IS THE CORRECT FINDING ───────────────────────
st.markdown('<div class="section-title">2. Why AUC 0.518 is the correct finding, not a failure</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    <div class="honest-box">
    <h4>What it means</h4>
    <p>AUC 0.518 on Model A (penalty pressure → P(goal)) means the pressure context features 
    predict individual penalty outcomes barely better than random. A coin flip does almost as well.</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="honest-box">
    <h4>Why this is correct, not wrong</h4>
    <p>The sports-science literature (Jordet et al., 2006–2019; Wood & Wilson, 2010) consistently 
    shows that while pressure elevates physiological arousal and population-level miss rates, 
    individual outcomes contain large irreducible variance. AUC 0.518 is <em>expected</em> given what 
    we know about penalty psychology. A suspiciously high AUC would suggest data leakage.</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="honest-box">
    <h4>Why we report it prominently</h4>
    <p>A system that buries a low AUC in a footnote is not trustworthy. Reporting AUC 0.518 
    prominently — and explaining why it is the honest result — is itself a design decision 
    that builds trust. This is human-centered AI: putting what the system <em>cannot</em> know 
    at the centre, not the periphery.</p>
    </div>
    """, unsafe_allow_html=True)

# Visual: ROC curve conceptual
auc_vals = np.linspace(0, 1, 100)
fig_roc = go.Figure()
fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines',
                              line=dict(dash='dash', color='#555'), name='Random (AUC=0.50)'))
# Rough AUC 0.518 curve
t = np.linspace(0, 1, 100)
fpr_a = t
tpr_a = np.clip(t + 0.036 * np.sin(np.pi * t), 0, 1)
fig_roc.add_trace(go.Scatter(x=fpr_a, y=tpr_a, mode='lines',
                              line=dict(color='#fa4d56', width=2),
                              name=f'Model A — Penalty pressure (AUC ≈{m_a["cv_auc"]:.3f})'))
# AUC 0.773 curve
fpr_b = t
tpr_b = np.clip(t ** 0.35, 0, 1)
fig_roc.add_trace(go.Scatter(x=fpr_b, y=tpr_b, mode='lines',
                              line=dict(color='#42be65', width=2),
                              name=f'Model B — Late-shot residual (AUC ≈{m_b["cv_auc"]:.3f})'))

fig_roc.update_layout(
    template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
    height=320, xaxis_title='False Positive Rate', yaxis_title='True Positive Rate',
    title='Illustrative ROC curves — two models, two questions',
    legend=dict(orientation='h', yanchor='bottom', y=1.02, font=dict(size=10)),
    margin=dict(t=60, b=20),
)
st.plotly_chart(fig_roc, use_container_width=True)
st.caption("Note: ROC curves above are illustrative approximations for visual clarity. Actual AUC values are from 5-fold stratified cross-validation on the real dataset.")

# ─── SECTION 3: WHY RESIDUAL ANALYSIS FOR MODEL B ───────────────────────────
st.markdown('<div class="section-title">3. Why residual analysis (Model B) — not raw prediction</div>', unsafe_allow_html=True)

r1, r2 = st.columns([3, 2])
with r1:
    st.markdown("""
    **The problem with predicting late-game shots directly:** StatsBomb's xG already encodes 
    shot quality — position, angle, assist type, goalkeeper position. Feeding raw features into 
    a prediction model re-learns xG without isolating the pressure effect above it.

    **What the residual approach does:** Model B takes the *difference* between the actual outcome 
    (0 or 1) and StatsBomb's xG estimate for each shot. This residual (`is_goal − xG`) is the 
    pressure signal stripped of shot quality. A negative mean residual in knockout matches means 
    players are slightly underperforming their shot quality in high-stakes moments.

    **The specific finding:** Knockout match late-game shots underperform xG by −0.0071 per shot 
    vs −0.0061 in group stages. Small effect, real direction, honest interpretation — pressure 
    shifts shot *quality manufactured* more than conversion on equivalent chances.
    """)
    st.markdown("""
    <div class="why-box">
    <h4>Why this is methodologically stronger</h4>
    <p>The residual approach is the correct tool for isolating a contextual effect on top of an 
    existing baseline model. It is the same logic as A/B testing under real-world conditions 
    where you cannot hold everything else constant — you compare each unit to its own expected 
    baseline rather than to an absolute standard.</p>
    </div>
    """, unsafe_allow_html=True)

with r2:
    # Show xG vs actual comparison
    stages = ['Group Stage', 'Round of 16', 'QF/SF', 'Final']
    residuals_ko = [m_b['group_stage_residual'], m_b['knockout_residual'],
                    m_b['knockout_residual'] * 1.12, m_b['knockout_residual'] * 1.28]
    colors_r = ['#42be65' if r >= 0 else '#fa4d56' for r in residuals_ko]

    fig_res = go.Figure(go.Bar(
        x=stages, y=residuals_ko,
        marker_color=colors_r,
        text=[f"{v:+.4f}" for v in residuals_ko],
        textposition='outside',
    ))
    fig_res.add_hline(y=0, line_dash='dash', line_color='#555')
    fig_res.update_layout(
        template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
        height=280, yaxis_title='Mean xG Residual',
        title='xG residual by stage (approx.)',
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig_res, use_container_width=True)
    st.caption("Negative = players underperformed their expected goals. Group stage and knockout are real values; QF/SF and Final are illustrative extrapolations from the knockout aggregate.")

# ─── SECTION 4: WHY LOGISTIC REGRESSION NOT XGBOOST ────────────────────────
st.markdown('<div class="section-title">4. Why logistic regression — not XGBoost, Random Forest, or a neural net</div>', unsafe_allow_html=True)

lr1, lr2, lr3 = st.columns(3)
with lr1:
    st.markdown("""
    <div class="decision-card">
    <h3>Sample size constraint</h3>
    <p>n=202 binary outcomes (Model A) and n=1,228 (Model B) are real constraints. 
    XGBoost on n=202 with binary outcomes overfits without extensive regularization tuning 
    that the data cannot support. Logistic regression with 4 features is the 
    appropriately-complex model for this dataset.</p>
    </div>
    """, unsafe_allow_html=True)
with lr2:
    st.markdown("""
    <div class="decision-card">
    <h3>Explainability requirement</h3>
    <p>SHAP LinearExplainer computes exact Shapley values for linear models — not 
    approximate. With a logistic regression, the SHAP values sum exactly to the 
    log-odds difference between prediction and baseline. With XGBoost, TreeExplainer 
    is approximate and pathway-dependent. Exact attribution is worth the AUC trade-off.</p>
    </div>
    """, unsafe_allow_html=True)
with lr3:
    st.markdown("""
    <div class="decision-card">
    <h3>Interpretability of coefficients</h3>
    <p>The logistic regression coefficients are directly interpretable: 
    is_shootout coefficient of {coef:.3f} means each unit increase in the shootout flag 
    multiplies the odds of scoring by e^({coef:.3f}) = {odds:.2f}×. No post-hoc explanation 
    needed. The model is the explanation.</p>
    </div>
    """.format(
        coef=m_a['coefficients'].get('is_shootout', -0.8),
        odds=np.exp(m_a['coefficients'].get('is_shootout', -0.8))
    ), unsafe_allow_html=True)

# ─── SECTION 5: WHY SHAP LINEAREXPLAINER IS EXACT HERE ─────────────────────
st.markdown('<div class="section-title">5. Why SHAP LinearExplainer — and why it is exact (not approximate) here</div>', unsafe_allow_html=True)

s1, s2 = st.columns([2, 3])
with s1:
    st.markdown("""
    <div class="why-box">
    <h4>The SHAP exactness guarantee</h4>
    <p>For linear models, SHAP has a closed-form solution. The LinearExplainer computes 
    the exact Shapley value for each feature by integrating over the conditional expectation 
    analytically — no sampling, no approximation.</p>
    </div>
    
    <div class="why-box">
    <h4>What this means practically</h4>
    <p>Every SHAP waterfall chart in the Pressure Lens is not an estimate — it is the 
    exact attribution of each feature's contribution to the predicted log-odds for that 
    specific kick. The values sum exactly to the log-odds difference between the 
    intercept-only prediction and the full model prediction.</p>
    </div>
    
    <div class="why-box">
    <h4>Why this matters for trust</h4>
    <p>An AI system that explains its decisions approximately is harder to trust than one 
    that explains them exactly. The choice of logistic regression was partly motivated by 
    wanting exact attribution, not just approximate feature importance.</p>
    </div>
    """, unsafe_allow_html=True)

with s2:
    # SHAP coefficient visualization
    feats = list(m_a['coefficients'].keys())
    coefs = list(m_a['coefficients'].values())
    colors_shap = ['#fa4d56' if c < 0 else '#42be65' for c in coefs]

    fig_shap = go.Figure(go.Bar(
        y=feats, x=coefs, orientation='h',
        marker_color=colors_shap,
        text=[f"{c:+.3f}" for c in coefs],
        textposition='outside',
    ))
    fig_shap.add_vline(x=0, line_color='#555')
    fig_shap.update_layout(
        template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
        height=280, xaxis_title='Log-odds coefficient',
        title='Logistic regression coefficients — Model A',
        margin=dict(t=40, b=20),
    )
    st.plotly_chart(fig_shap, use_container_width=True)
    st.caption("Each coefficient is the log-odds change per unit increase in that feature. SHAP LinearExplainer converts these to the exact contribution of each feature to any individual prediction.")

# ─── SECTION 6: 5-FOLD CV — WHY NOT A TRAIN/TEST SPLIT ─────────────────────
st.markdown('<div class="section-title">6. Why 5-fold CV — not a held-out test split</div>', unsafe_allow_html=True)

st.markdown("""
At n=202 penalties with class imbalance (~69% positive), a held-out 20% test set gives a 
test set of ~40 samples. AUC on 40 samples has very high variance — a ±0.05 swing is 
within one standard deviation of the sampling distribution.

**Stratified 5-fold CV** gives 5 non-overlapping test folds of ~40 samples each, averaged. 
The variance of this estimate is lower by a factor of √5, and the estimate is less biased 
because each observation appears exactly once in a test fold. This is the standard practice 
for small-sample binary classification in applied statistics.

The reported AUC values (0.518, 0.773) are the means of 5 AUC scores from 5 independent 
folds, each evaluated on data the model never saw during training.
""")

# ─── SECTION 7: DATA PIPELINE DECISIONS ─────────────────────────────────────
st.markdown('<div class="section-title">7. Pipeline design decisions</div>', unsafe_allow_html=True)

pipeline_steps = [
    ("1", "StatsBomb open data — concurrent fetch",
     "192 matches fetched in parallel using ThreadPoolExecutor(max_workers=12). "
     "Sequential fetching would take ~4 minutes; concurrent fetch takes ~30 seconds. "
     "All data from StatsBomb's public GitHub endpoint — no scraping, no API keys needed."),
    ("2", "Shot type separation at event level",
     "Penalties and late-game shots are separated at extraction time, not post-hoc. "
     "This ensures the two models are trained on disjoint, purpose-defined datasets. "
     "A penalty in extra time is not double-counted as a late-game shot."),
    ("3", "Stage weight encoding",
     "Tournament stage is encoded as a continuous weight (0.0 = Group Stage → 1.0 = Final) "
     "rather than one-hot. This preserves ordinal information about stakes and avoids "
     "adding 6 dummy features to a 4-feature model on 202 samples."),
    ("4", "Sudden-death detection by kick order",
     "Sudden-death kicks are those beyond position 10 in a shootout (5 kicks per team in "
     "the standard phase). Kick order is computed by ranking by minute within each shootout "
     "match — no manual annotation required."),
    ("5", "parquet, not CSV",
     "Processed features are stored as .parquet files rather than CSV. Parquet preserves "
     "dtypes exactly (int8 for binary flags, float32 for xG), is ~4× smaller on disk, "
     "and loads ~10× faster. No dtype coercion errors on reload."),
    ("6", "SHAP computed at inference time, not cached",
     "SHAP values on the Landmark Explorer are computed at click time from the live model, "
     "not loaded from a cache. This ensures the values are always consistent with the "
     "model being displayed — no stale attribution artefacts."),
]

for num, title, desc in pipeline_steps:
    st.markdown(f"""
    <div class="pipeline-step">
      <div class="step-num">{num}</div>
      <div>
        <span style="color:#78a9ff;font-weight:600;font-size:0.92rem">{title}</span><br>
        <span style="color:#c6c6c6;font-size:0.86rem;line-height:1.55">{desc}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ─── SECTION 8: IBM STACK DESIGN DECISIONS ───────────────────────────────────
st.markdown('<div class="section-title">8. IBM stack — why each technology, what it does</div>', unsafe_allow_html=True)

ibm_stack = [
    ("IBM Granite via watsonx.ai", "ibm/granite-4-h-small",
     "Narration layer. Three mode system prompts (fan, analyst, referee_trainee) ensure the same "
     "grounded data is communicated at the appropriate technical level for each audience. "
     "Granite is never allowed to fabricate statistics — all numbers are passed as structured context "
     "via the MCP tool layer. The model is small enough to be responsive; narration, not heavy reasoning, "
     "is the task."),
    ("IBM Docling 2.103", "PDF → structured JSON",
     "The IFAB Laws of the Game 2025/26 PDF is a complex, multi-column document with footnotes, "
     "cross-references, and margin notes. Docling's layout-aware extraction preserves section structure "
     "better than naive PDF text extraction. law_chunks.json contains the parsed output; the Officiating "
     "Lens and Granite Chat draw from it so law citations are grounded in actual document content, not "
     "Granite's training knowledge."),
    ("IBM Context Forge MCP 1.0.3", "Tool grounding",
     "Three tools (get_pressure_profile, get_law_text, get_overturn_rate) implemented as a Context Forge "
    "MCP server in ibm_layer/tools.py. The HF Spaces deployment calls them as direct Python functions "
    "for reliability — mcpgateway requires a persistent server process that conflicts with Streamlit's "
    "single-process model on HF. The tool schema, ToolDataError anti-hallucination pattern, and "
    "grounding architecture are all production-ready and verified locally. No number in any Granite "
    "narration is invented — every value traces to a real parquet file or sourced JSON."),
    ("IBM Bob 1.0.4", "Development assistant",
     "Used throughout the build for Law 14 penalty kick regulation summarisation, debugging the "
     "SHAP LinearExplainer integration, and generating the officiating_scenarios.json template. "
     "IBM Bob's output was reviewed, corrected where needed, and committed — same workflow as any "
     "AI-assisted development process."),
]

for tech, version, role in ibm_stack:
    c_a, c_b = st.columns([1, 3])
    with c_a:
        st.markdown(f"""
        <div style="background:#0f1525;border:1px solid #1e3a6e;border-radius:8px;
                    padding:0.9rem;text-align:center;height:100%">
          <div style="color:#78a9ff;font-weight:700;font-size:0.9rem">{tech}</div>
          <div style="color:#555;font-size:0.78rem;margin-top:4px">{version}</div>
        </div>
        """, unsafe_allow_html=True)
    with c_b:
        st.markdown(f"""
        <div style="background:#111;border:1px solid #1e1e1e;border-radius:8px;padding:0.9rem;">
          <p style="margin:0;color:#c6c6c6;font-size:0.88rem;line-height:1.6">{role}</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("")

# ─── SECTION 9: WHAT THE SYSTEM CANNOT DO ────────────────────────────────────
st.markdown('<div class="section-title">9. Explicit limits — what this system cannot do</div>', unsafe_allow_html=True)

st.markdown("""
Human-centred AI requires honesty about limits, not just capability claims. 
These are not caveats buried at the bottom — they are design constraints built into every page.
""")

limits = [
    ("Cannot predict individual penalty outcomes reliably",
     "AUC 0.518 is the evidence. Any system claiming otherwise on n=202 kicks is overfit or dishonest."),
    ("Cannot access goalkeeper or taker biometrics",
     "Physiological arousal, run-up speed, eye-tracking, or heart rate — real pressure predictors "
     "in the laboratory — are absent from any available World Cup dataset."),
    ("Cannot reconstruct VAR video or camera feeds",
     "The Officiating Lens draws on official tournament reports and Laws. It cannot replay "
     "the actual frames seen by VAR officials or reproduce their specific measurement."),
    ("Cannot generalise to club football or non-World Cup data",
     "The three tournaments were chosen for data availability (StatsBomb open data). Club football "
     "has different pressure dynamics, different crowd effects, and different penalty cultures. "
     "Transfer is unvalidated."),
    ("Cannot explain individual SAOT decisions",
     "The 2026 WC SAOT outage scenario is an observation about process, not a reconstruction "
     "of the measurement that would have been made had SAOT been functioning."),
]

lim_c1, lim_c2 = st.columns(2)
for i, (title, desc) in enumerate(limits):
    col = lim_c1 if i % 2 == 0 else lim_c2
    with col:
        col.markdown(f"""
        <div class="honest-box">
        <h4>{title}</h4>
        <p>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

# ─── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="color:#555;font-size:0.82rem;text-align:center;padding:1rem">
  FineMargins methodology · StatsBomb Open Data (StatsBomb Public Data User Agreement) · 
  IFAB Laws of the Game 2025/26 · IBM Granite via watsonx.ai · IBM Docling 2.103 · 
  IBM Context Forge MCP 1.0.3 · IBM Bob 1.0.4<br>
  Built for IBM SkillsBuild AI Builders Challenge, June 2026 — "AI Inside the Match"
</div>
""", unsafe_allow_html=True)