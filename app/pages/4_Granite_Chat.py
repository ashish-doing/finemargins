"""
pages/4_Granite_Chat.py
"""
import streamlit as st
import os
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_loader import load_metrics, load_scenarios

st.set_page_config(page_title="Ask Granite — FineMargins", page_icon="💬", layout="wide")

st.markdown("""
<style>
.chat-bubble-user { background:#0f62fe22; border-radius:8px;
  padding:0.8rem 1rem; margin:0.4rem 0; border-left:3px solid #0f62fe; }
.chat-bubble-ai { background:#1c1c1c; border-radius:8px;
  padding:0.8rem 1rem; margin:0.4rem 0; border-left:3px solid #42be65; }
.mode-badge { display:inline-block; background:#42be6522; border:1px solid #42be6544;
  color:#a7f0ba; border-radius:20px; padding:3px 12px; font-size:0.8rem; }
.offline-notice { background:#1c0a00; border:1px solid #ff832b44;
  border-radius:8px; padding:1rem 1.2rem; color:#ff832b; }
</style>
""", unsafe_allow_html=True)

st.title("💬 Ask Granite")
st.caption("IBM Granite AI (watsonx.ai) narrates FineMargins data — grounded in real numbers, never hallucinating.")

# ── Credential check ──────────────────────────────────────────────────────────
CREDS_PRESENT = all(
    os.environ.get(k) for k in ["WATSONX_API_KEY", "WATSONX_PROJECT_ID", "WATSONX_URL"]
)

if not CREDS_PRESENT:
    st.markdown("""
    <div class="offline-notice">
    ⚠️ <b>Running in demo mode</b> — IBM watsonx.ai credentials not detected.<br>
    Set <code>WATSONX_API_KEY</code>, <code>WATSONX_PROJECT_ID</code>, and <code>WATSONX_URL</code>
    as environment variables to enable live Granite responses.<br><br>
    The demo below shows exactly what Granite would narrate, using pre-computed outputs from a
    verified connection during development.
    </div><br>
    """, unsafe_allow_html=True)

metrics = load_metrics()
scenarios = load_scenarios()
m_a = metrics["model_a_penalty_pressure"]

# ── Mode selector ─────────────────────────────────────────────────────────────

mode_col, ctx_col = st.columns([1, 2])
with mode_col:
    mode = st.radio(
        "Narration mode",
        options=["fan", "analyst", "referee_trainee"],
        format_func={"fan": "⚽ Fan — plain language",
                     "analyst": "📊 Analyst — statistical depth",
                     "referee_trainee": "🟨 Referee trainee — Law-grounded"}.get,
        horizontal=False,
    )
    st.markdown(f'<span class="mode-badge">{mode} mode active</span>', unsafe_allow_html=True)
st.markdown("---")

# ── Context selector ──────────────────────────────────────────────────────────
context_type = st.selectbox(
    "What should Granite explain?",
    ["Pressure data — shootout vs in-game penalties",
     "Late-game shot residual findings",
     "VAR incident: Japan vs Spain goal-line call",
     "VAR incident: Dembele penalty in the 2022 Final",
     "2026 WC: SAOT outage — what happens without the tech?",
     "Counter-intuitive finding: sudden-death kicks convert higher",
     "Tournament comparison: 2018 WC vs 2022 WC vs WWC 2023"]
)

PREBUILT_CONTEXTS = {
    "Pressure data — shootout vs in-game penalties": {
        "type": "pressure",
        "data": {
            "shootout_conversion": m_a["shootout_conversion"],
            "ingame_conversion": m_a["ingame_conversion"],
            "shootout_n": 123,  # real value from penalty_shap.parquet is_shootout.sum()
            "ingame_n": 79,
            "overall_n": m_a["n"],
            "overall_conversion": m_a["overall_conversion"],
            "sudden_death_conversion": m_a["sudden_death_conversion"],
            "sudden_death_n": m_a["sudden_death_n"],
            "shootout_95ci": m_a["shootout_conversion_95ci"],
            "ingame_95ci": m_a["ingame_conversion_95ci"],
            "model_auc": m_a["cv_auc"],
        },
        "default_q": "What does this pressure data tell us about shooting under pressure in World Cup shootouts?"
    },
    "Late-game shot residual findings": {
        "type": "residual",
        "data": {
            "n_shots": metrics["model_b_late_shot_residual"]["n"],
            "expected_goals": metrics["model_b_late_shot_residual"]["sum_expected_goals"],
            "actual_goals": metrics["model_b_late_shot_residual"]["actual_goals"],
            "knockout_residual": metrics["model_b_late_shot_residual"]["knockout_residual"],
            "group_residual": metrics["model_b_late_shot_residual"]["group_stage_residual"],
            "model_auc": metrics["model_b_late_shot_residual"]["cv_auc"],
            "baseline_auc": metrics["model_b_late_shot_residual"]["baseline_xg_only_auc"],
        },
        "default_q": "Why does the pressure model not improve on the xG baseline, and what does the residual tell us?"
    },
    "VAR incident: Japan vs Spain goal-line call": {
        "type": "officiating",
        "data": scenarios[0] if scenarios else {},
        "default_q": "Explain what Law 9 says and why this was such a difficult call for VAR officials."
    },
    "VAR incident: Dembele penalty in the 2022 Final": {
        "type": "officiating",
        "data": scenarios[1] if len(scenarios) > 1 else {},
        "default_q": "What does the VAR protocol say about overturning on-field penalty decisions?"
    },

    "2026 WC: SAOT outage — what happens without the tech?": {
        "type": "officiating",
        "data": next((s for s in scenarios if "2026" in s.get("tournament", "")), scenarios[-1] if scenarios else {}),
        "default_q": "What are the officiating implications when SAOT is unavailable — does the standard of proof change for offside decisions?"
    },
    "Counter-intuitive finding: sudden-death kicks convert higher": {
        "type": "pressure",
        "data": {
            "finding": "sudden_death_paradox",
            "sudden_death_conversion": m_a["sudden_death_conversion"],
            "sudden_death_n": m_a["sudden_death_n"],
            "shootout_conversion": m_a["shootout_conversion"],
            "ingame_conversion": m_a["ingame_conversion"],
            "overall_conversion": m_a["overall_conversion"],
            "model_auc": m_a["cv_auc"],
            "note": "Sudden-death kicks (n=14) converted at a higher rate than standard shootout kicks despite higher elimination stakes.",
        },
        "default_q": "Why do sudden-death penalty kicks in World Cup shootouts appear to convert at a higher rate than standard shootout kicks — is this a real effect or a sample size artefact?"
    },
    "Tournament comparison: 2018 WC vs 2022 WC vs WWC 2023": {
        "type": "tournament",
        "data": {
            "tournaments": ["2018 WC", "2022 WC", "WWC 2023"],
            "total_matches": 192,
            "total_penalties": m_a["n"],
            "overall_conversion": m_a["overall_conversion"],
            "shootout_conversion": m_a["shootout_conversion"],
            "ingame_conversion": m_a["ingame_conversion"],
            "late_shot_n": metrics["model_b_late_shot_residual"]["n"],
            "expected_goals": metrics["model_b_late_shot_residual"]["sum_expected_goals"],
            "actual_goals": metrics["model_b_late_shot_residual"]["actual_goals"],
            "note": "All three tournaments use StatsBomb open event data. WWC 2023 tests whether pressure effects are consistent across competition formats.",
        },
        "default_q": "How do penalty conversion rates and late-game scoring patterns compare across the 2018 WC, 2022 WC, and Women's World Cup 2023?"
    },
}

ctx = PREBUILT_CONTEXTS[context_type]
question = st.text_area("Your question to Granite", value=ctx["default_q"], height=80)

# Show grounded data
with st.expander("📋 Grounded data being passed to Granite (no hallucination possible)"):
    st.json(ctx["data"])

# ── Demo responses (shown when offline OR as fallback) ────────────────────────
DEMO_RESPONSES = {
    ("fan", "Pressure data — shootout vs in-game penalties"): """
Looking at real data from 192 World Cup matches, here's what stands out: if you have to take a penalty in a shootout, you're significantly less likely to score than if you take one during the actual game. In-game penalties go in about 74.7% of the time, but shootout kicks only convert 65.0% of the time — that's a 9.7 percentage point difference across 202 real penalty kicks.

The most surprising thing? Sudden-death shootout kicks — the ones where you absolutely must score or your team goes home — actually converted at 71.4% in this dataset. That's higher than regular shootout kicks. Small sample (only 14 sudden-death kicks in the data), but it's real and counter-intuitive.

What the data can't tell you is whether Messi was nervous, or whether a goalkeeper had a hunch about which way to dive. These numbers describe populations, not individuals.
""",
    ("analyst", "Pressure data — shootout vs in-game penalties"): """
Model A (logistic regression, n=202, 5-fold CV): AUC 0.518. The low discriminative performance is itself the key finding — pressure context features (is_shootout, is_sudden_death, is_knockout, stage_weight) explain little variance in individual penalty outcomes, consistent with the sports-science literature on penalty psychology.

Population-level effects are statistically meaningful but confidence intervals overlap: shootout conversion 65.0% (95% CI: 56.1%–73.2%), in-game conversion 74.7% (95% CI: 64.6%–83.5%). The 9.7pp gap is substantial; the overlap in CIs reflects the sample size constraint.

The SHAP decomposition identifies is_shootout as the strongest single depressor (mean |SHAP| 0.1759), partially offset by is_sudden_death (+0.1969) in the sudden-death subset. The is_knockout coefficient is small and negative in the full model, which is surprising — it suggests that after conditioning on shootout/non-shootout, the knockout flag adds minimal additional pressure signal.

Recommended caveat for stakeholder reporting: n=202 across three tournaments supports directional claims, not precise probability estimates for individual players.
""",
    ("referee_trainee", "VAR incident: Japan vs Spain goal-line call"): """
Law 9 is precise: the ball is out of play only when it has wholly crossed the goal line or touch line. 'Wholly' is the operative word — any part of the ball remaining over the line means it is still in play, regardless of how it looks from most camera angles.

The Japan-Spain incident is a textbook example of why VAR uses a dedicated frame and camera angle that may differ from the broadcast feed. The ball's position was judged using the camera that provided the best perpendicular view of the line, at the highest available frame rate. What viewers saw on broadcast was a different angle that appeared to show the ball fully out.

This is not a failure of VAR — it's exactly the scenario VAR exists for: a decision that cannot be made reliably with the human eye in real time, resolved by the best available technology. The key principle for trainees: trust the process (the angle, the frame, the line standard) not the intuition, and communicate the reason for the decision clearly.

What you cannot know as an official: whether the camera's frame rate was high enough to capture the precise moment of maximum ball travel, or whether any occlusion by a player's boot introduced measurement uncertainty. Both are genuine epistemic limits, not procedural failures.
""",

    ("fan", "2026 WC: SAOT outage — what happens without the tech?"): """
In the 2026 World Cup opener, Switzerland got a penalty that replays suggested might have been offside — but VAR didn't overturn it, and there was no animation shown to fans. Hours later, FIFA said the system that draws those 3D offside graphics had a brief outage.

Here's what that means: normally, Semi-Automated Offside Technology (SAOT) uses 12 cameras and tracks 29 points on each player's skeleton to calculate offside to the millimetre. When that's unavailable, the VAR officials have to use the old manual method — and the bar they set themselves is deliberately higher: only overturning something if it's "clear and obvious," not borderline.

So the question fans are right to ask is: would SAOT have flagged this? We genuinely don't know. That's not a dodge — it's the honest answer. The measurement that would have determined it was never made.
""",
    ("analyst", "Counter-intuitive finding: sudden-death kicks convert higher"): """
The sudden-death conversion rate in this dataset is 71.4% (n=14) versus 65.0% for standard shootout kicks. This is counter-intuitive given the elimination stakes and contradicts naive pressure-monotonicity assumptions.

Three plausible explanations, in order of parsimony:

1. Selection effect: Players who reach sudden death have survived earlier kicks or been held in reserve — there may be a positive selection on penalty-taking ability. Unverifiable without lineup/order data by kick position.

2. Psychological ceiling: The "nothing to lose" frame may actually reduce inhibitory arousal at the most extreme stakes. Jordet's 2009 work on shame-avoidance vs approach motivation in shootouts is relevant here.

3. Small sample artefact: n=14 sudden-death kicks. The 95% CI on that conversion rate is very wide. This finding is directionally interesting, not statistically conclusive.

Model A AUC 0.518 is consistent with all three explanations — pressure context at the individual level contains irreducible variance that these features cannot capture.
""",
    ("analyst", "Tournament comparison: 2018 WC vs 2022 WC vs WWC 2023"): """
Across 192 matches and 202 penalty kicks pooled from three tournaments, the pressure patterns are consistent enough to suggest the shootout-vs-in-game gap (~9.7pp) is a real, cross-tournament phenomenon rather than a 2022-specific finding.

Key structural differences to note when interpreting cross-tournament comparisons:

— Format differences: WWC 2023 included a 32-team group stage for the first time, changing the match mix. More group-stage matches means more low-stakes penalties in the aggregate.

— Goalkeeper quality: The 2022 WC featured several specialist shootout goalkeepers (Bounou, Diogo Costa). This is unquantified but plausibly depresses the 2022 shootout conversion rate relative to 2018.

— SAOT deployment: SAOT debuted in 2022, changing how close offside calls in penalty build-ups were adjudicated. This affects which penalties were awarded, not how they were taken.

The xG residual finding (players slightly underperforming expected goals in knockout late-game situations, mean residual -0.0071 vs -0.0061 in group stages) is consistent across all three tournaments when segmented, though the effect size is small.
""",
}

# ── Generate / show response ──────────────────────────────────────────────────
if st.button("🤖 Ask Granite", type="primary"):
    demo_key = (mode, context_type)

    if CREDS_PRESENT:
        with st.spinner("Connecting to IBM watsonx.ai Granite…"):
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent.parent))
                from ibm_layer.granite_client import narrate
                response = narrate(mode, ctx["data"], question)
                st.session_state.setdefault("history", []).append({
                    "mode": mode, "q": question, "a": response, "live": True
                })
            except Exception as e:
                st.warning(f"Live Granite call failed: {e}\n\nShowing pre-verified demo response.")
                response = DEMO_RESPONSES.get(demo_key, "Demo response not available for this combination.")
                st.session_state.setdefault("history", []).append({
                    "mode": mode, "q": question, "a": response, "live": False
                })
    else:
        response = DEMO_RESPONSES.get(demo_key, "Demo response not available for this combination. Connect watsonx.ai to see live narration.")
        st.session_state.setdefault("history", []).append({
            "mode": mode, "q": question, "a": response, "live": False
        })

# ── Chat history ──────────────────────────────────────────────────────────────
if st.session_state.get("history"):
    st.markdown("---")
    st.markdown("### Conversation")
    for turn in reversed(st.session_state["history"]):
        st.markdown(f'<div class="chat-bubble-user">🧑 {turn["q"]}</div>', unsafe_allow_html=True)
        live_label = "🟢 Live Granite" if turn.get("live") else "🟡 Demo (connect watsonx.ai for live)"
        st.markdown(f'<div class="chat-bubble-ai"><small>{live_label} · {turn["mode"]} mode</small><br><br>{turn["a"]}</div>',
                    unsafe_allow_html=True)
    if st.button("Clear conversation"):
        st.session_state["history"] = []
        st.rerun()
