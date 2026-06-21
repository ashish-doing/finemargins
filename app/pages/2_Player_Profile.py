"""
pages/2_Player_Profile.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path
from sklearn.linear_model import LogisticRegression
import shap as shap_lib

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_loader import load_penalties, load_player_profiles, load_metrics

st.set_page_config(page_title="Player Profiles — FineMargins", page_icon="👤", layout="wide")

st.markdown("""
<style>
.player-hero { background:linear-gradient(135deg,#1a1a2e,#16213e);
  border-left:5px solid #0f62fe; border-radius:8px; padding:1.2rem 1.5rem; margin-bottom:1rem; }
.player-hero h2 { margin:0; font-size:1.8rem; }
.player-hero p { margin:0.3rem 0 0; color:#a8a8a8; }
.finding-box { background:#1c1c1c; border-left:4px solid #0f62fe;
  border-radius:6px; padding:0.9rem 1.1rem; margin:0.5rem 0; }
</style>
""", unsafe_allow_html=True)

st.title("👤 Player Profiles")
st.caption("159 players with at least one World Cup penalty across 2018 WC, 2022 WC, and Women's WC 2023.")

pen = load_penalties()
profiles = load_player_profiles()
metrics = load_metrics()

# ── Sidebar search ────────────────────────────────────────────────────────────
st.sidebar.header("🔎 Find a player")
search = st.sidebar.text_input("Search name", placeholder="Messi, Kane, Kerr…")
tournament_filter = st.sidebar.multiselect(
    "Tournament", options=pen['tournament'].unique().tolist(),
    default=pen['tournament'].unique().tolist()
)
min_penalties = st.sidebar.slider("Min. penalties taken", 1, 5, 1)

filtered = profiles[
    profiles['total_penalties'] >= min_penalties
]
if search:
    filtered = filtered[filtered['player'].str.contains(search, case=False, na=False)]
if tournament_filter:
    filtered = filtered[filtered['tournament'].isin(tournament_filter)]

# ── Overview table ─────────────────────────────────────────────────────────────
st.markdown("### All players in dataset")
display_cols = ['player', 'tournament', 'total_penalties', 'goals', 'conversion_rate',
                'shootout_n', 'shootout_goals', 'ingame_n', 'ingame_goals']

display = filtered[display_cols].rename(columns={
    'player': 'Player', 'tournament': 'Tournament',
    'total_penalties': 'Total', 'goals': 'Goals',
    'conversion_rate': 'Conv%',
    'shootout_n': 'SO Kicks', 'shootout_goals': 'SO Goals',
    'ingame_n': 'IG Kicks', 'ingame_goals': 'IG Goals'
})
display['Conv%'] = (display['Conv%'] * 100).round(1)

st.dataframe(
    display.sort_values('Total', ascending=False).reset_index(drop=True),
    use_container_width=True, height=320,
    column_config={
        "Conv%": st.column_config.ProgressColumn("Conv%", min_value=0, max_value=100, format="%.1f%%"),
        "Total": st.column_config.NumberColumn("Total", help="Total penalties taken"),
    }
)

st.markdown("---")

# ── Individual deep-dive ───────────────────────────────────────────────────────
st.markdown("### Deep dive — individual player")

top_players = filtered.sort_values('total_penalties', ascending=False)['player'].tolist()
if not top_players:
    st.warning("No players match the current filters.")
    st.stop()

selected_player = st.selectbox("Select player", top_players)
prow = profiles[profiles['player'] == selected_player].iloc[0]
player_kicks = pen[pen['player'] == selected_player]

st.markdown(f"""
<div class="player-hero">
  <h2>⚽ {selected_player}</h2>
  <p>Tournament: {prow.tournament} · Total penalties: {prow.total_penalties}</p>
</div>
""", unsafe_allow_html=True)

# KPI row
kc1, kc2, kc3, kc4, kc5 = st.columns(5)
kc1.metric("Total", int(prow.total_penalties))
kc2.metric("Goals", int(prow.goals))
kc3.metric("Conversion", f"{prow.conversion_rate:.1%}")
kc4.metric("In-game kicks", int(prow.ingame_n),
           delta=f"{int(prow.ingame_goals)} goals" if prow.ingame_n > 0 else None)
kc5.metric("Shootout kicks", int(prow.shootout_n),
           delta=f"{int(prow.shootout_goals)} goals" if prow.shootout_n > 0 else None)

lc, rc = st.columns(2)

with lc:
    st.markdown("#### Pressure breakdown for this player's kicks")
    if len(player_kicks) == 0:
        st.info("No kicks in dataset after current filter.")
    else:
        pk = player_kicks.copy()
        feat_a = ['is_shootout', 'is_sudden_death', 'is_knockout', 'stage_weight']
        X_all = pen[feat_a].values
        y_all = pen['is_goal'].values
        model = LogisticRegression(max_iter=1000).fit(X_all, y_all)
        probs = model.predict_proba(pk[feat_a].values)[:, 1]
        pk['predicted_prob'] = probs

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(1, len(pk)+1)),
            y=probs,
            mode='markers+lines',
            marker=dict(
                color=['#42be65' if g else '#fa4d56' for g in pk['is_goal']],
                size=14, symbol=['star' if s else 'circle' for s in pk['is_shootout']]
            ),
            line=dict(color='#555', width=1, dash='dot'),
            hovertemplate="Kick %{x}<br>Predicted P(goal): %{y:.1%}<br>" +
                          "Outcome: " + pk['outcome'] + "<extra></extra>",
        ))
        fig.add_hline(y=0.688, line_dash='dash', line_color='#888',
                      annotation_text="Dataset avg (68.8%)", annotation_position="bottom right")
        fig.update_layout(
            template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
            height=300, xaxis_title='Kick #', yaxis_title='P(Goal)',
            yaxis=dict(range=[0, 1.05], tickformat='.0%'),
            margin=dict(t=20, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("🟢 Scored · 🔴 Missed · ★ Shootout kick")

with rc:
    st.markdown("#### Where this player sits in the full dataset")

    all_probs = model.predict_proba(pen[feat_a].values)[:, 1]
    player_probs = model.predict_proba(player_kicks[feat_a].values)[:, 1] if len(player_kicks) > 0 else []

    fig2 = go.Figure()
    fig2.add_trace(go.Histogram(
        x=all_probs, nbinsx=20, name='All kickers',
        marker_color='#393939', opacity=0.7
    ))
    if len(player_probs) > 0:
        for pp in player_probs:
            fig2.add_vline(x=pp, line_color='#0f62fe', line_width=2)
        fig2.add_trace(go.Scatter(
            x=player_probs, y=[0]*len(player_probs),
            mode='markers', name=selected_player.split()[0],
            marker=dict(color='#0f62fe', size=12, symbol='diamond')
        ))
    fig2.update_layout(
        template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
        height=300, xaxis_title='Pressure-adjusted P(Goal)',
        yaxis_title='Count', margin=dict(t=20, b=20)
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── SHAP breakdown for the hardest kick ────────────────────────────────────────
if len(player_kicks) >= 1:
    st.markdown("#### SHAP attribution — hardest kick this player faced")
    hardest_idx = player_kicks['model_prob'].idxmin()
    hardest = player_kicks.loc[hardest_idx]

    shap_data = {
        'is_shootout': hardest['is_shootout'],
        'is_sudden_death': hardest['is_sudden_death'],
        'is_knockout': hardest['is_knockout'],
        'stage_weight': hardest['stage_weight'],
    }
    shap_vals = {
        'is_shootout': float(hardest['shap_is_shootout']),
        'is_sudden_death': float(hardest['shap_is_sudden_death']),
        'is_knockout': float(hardest['shap_is_knockout']),
        'stage_weight': float(hardest['shap_stage_weight']),
    }
    base_val = float(hardest['shap_base'])

    st.markdown(f"""
    <div class="finding-box">
    <b>Stage:</b> {hardest['stage']} · <b>Period:</b> {int(hardest['period'])} ·
    <b>Outcome:</b> {hardest['outcome']} ·
    <b>Pressure-adjusted P(Goal):</b> {float(hardest['model_prob']):.1%}
    </div>""", unsafe_allow_html=True)

    wf = go.Figure(go.Waterfall(
        orientation="h",
        measure=["absolute"] + ["relative"] * 4 + ["total"],
        x=[base_val] + list(shap_vals.values()) + [float(hardest['model_prob'])],
        y=["Base rate"] + list(shap_vals.keys()) + ["Final P(Goal)"],
        connector={"line": {"color": "#393939"}},
        increasing={"marker": {"color": "#fa4d56"}},
        decreasing={"marker": {"color": "#42be65"}},
        totals={"marker": {"color": "#0f62fe"}},
        texttemplate="%{x:.3f}",
    ))
    wf.update_layout(
        template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
        height=300, margin=dict(t=20, b=20)
    )
    st.plotly_chart(wf, use_container_width=True)

# ── Compare two players ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### ⚖️ Head-to-head pressure comparison")

ca, cb = st.columns(2)
with ca:
    p1 = st.selectbox("Player 1", top_players, index=0, key="p1")
with cb:
    p2_opts = [p for p in top_players if p != p1]
    p2 = st.selectbox("Player 2", p2_opts, index=0, key="p2")

def player_summary(name):
    row = profiles[profiles['player'] == name].iloc[0]
    kicks = pen[pen['player'] == name]
    probs = model.predict_proba(kicks[feat_a].values)[:, 1] if len(kicks) > 0 else []
    return row, probs

r1, pr1 = player_summary(p1)
r2, pr2 = player_summary(p2)

fig_cmp = go.Figure()
for name, probs, color in [(p1, pr1, '#0f62fe'), (p2, pr2, '#fa4d56')]:
    if len(probs) > 0:
        fig_cmp.add_trace(go.Box(
            y=probs, name=name.split()[-1], marker_color=color,
            boxpoints='all', jitter=0.4, pointpos=0
        ))
fig_cmp.add_hline(y=0.688, line_dash='dash', line_color='#888',
                   annotation_text="Dataset avg", annotation_position="right")
fig_cmp.update_layout(
    template='plotly_dark', plot_bgcolor='#0d0d0d', paper_bgcolor='#0d0d0d',
    height=360, yaxis_title='Pressure-adjusted P(Goal)',
    yaxis=dict(tickformat='.0%'), margin=dict(t=20, b=20)
)
st.plotly_chart(fig_cmp, use_container_width=True)

hh_cols = st.columns(2)
for col, (name, row) in zip(hh_cols, [(p1, r1), (p2, r2)]):
    with col:
        st.markdown(f"""
        <div class="finding-box">
        <b>{name.split()[0] if len(name.split())>0 else name}</b><br>
        Total: {int(row.total_penalties)} · Conv: {row.conversion_rate:.1%}<br>
        Shootout: {int(row.shootout_n)} kicks, {int(row.shootout_goals)} goals
        ({row.shootout_goals/row.shootout_n:.0%} if row.shootout_n > 0 else 'N/A')<br>
        In-game: {int(row.ingame_n)} kicks, {int(row.ingame_goals)} goals
        </div>""", unsafe_allow_html=True)
