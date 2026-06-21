"""
pages/3_Officiating_Lens.py
"""
import streamlit as st
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.data_loader import load_scenarios

st.set_page_config(page_title="Officiating Lens — FineMargins", page_icon="🟨", layout="wide")

st.markdown("""
<style>
.var-card { background:#1a1a1a; border:1px solid #393939; border-radius:10px;
  padding:1.4rem 1.6rem; margin-bottom:1rem; }
.law-box { background:#0f172a; border-left:4px solid #0f62fe;
  border-radius:6px; padding:0.9rem 1.1rem; margin:0.7rem 0; font-size:0.9rem; }
.unknown-box { background:#1c0a00; border-left:4px solid #ff832b;
  border-radius:6px; padding:0.9rem 1.1rem; margin:0.7rem 0; }
.badge { display:inline-block; background:#0f62fe22; border:1px solid #0f62fe44;
  color:#78a9ff; border-radius:4px; padding:2px 10px; font-size:0.78rem; margin:2px; }
</style>
""", unsafe_allow_html=True)

st.title("🟨 Officiating Lens")
st.caption("Real VAR decisions from World Cup history — explained using the actual Laws of the Game and historical data.")

st.markdown("""
> This lens is deliberately **not a prediction engine.** It doesn't tell you what
> the correct call was. It tells you what Law applies, what the historical base
> rate for that category of review is, and what the system fundamentally cannot know.
> That distinction is the whole point.
""")

VAR_STATS = {
    "Overall 2022 WC VAR checks": {"total": 22, "overturned": 6, "source": "FIFA 2022 WC Technical Report"},
    "Penalty decisions checked": {"total": 9, "overturned": 5, "source": "FIFA 2022 WC Technical Report"},
    "Red card checks": {"total": 5, "overturned": 1, "source": "FIFA 2022 WC Technical Report"},
    "Goal checks (offside/foul)": {"total": 8, "overturned": 0, "source": "FIFA 2022 WC Technical Report"},
}

st.markdown("### 📊 2022 World Cup VAR at a glance")
cols = st.columns(len(VAR_STATS))
for col, (label, stat) in zip(cols, VAR_STATS.items()):
    rate = stat['overturned'] / stat['total']
    col.metric(label, f"{stat['overturned']}/{stat['total']}", f"{rate:.0%} overturn rate")
    col.caption(stat['source'])

st.markdown("---")

scenarios = load_scenarios()

cat_icons = {
    "penalty": "🥅",
    "goal_line": "📏",
    "offside": "🚩",
    "handball": "✋",
    "red_card": "🟥",
}

selected_id = st.radio(
    "Choose an incident to examine:",
    options=[s['scenario_id'] for s in scenarios],
    format_func=lambda sid: next(
        f"{cat_icons.get(s['category'],'⚽')} {s['title']}"
        for s in scenarios if s['scenario_id'] == sid
    ),
    horizontal=True,
)

scenario = next(s for s in scenarios if s['scenario_id'] == selected_id)

st.markdown(f"""
<div class="var-card">
  <h3>{cat_icons.get(scenario['category'],'⚽')} {scenario['title']}</h3>
  <span class="badge">{scenario['tournament']}</span>
  <span class="badge">{scenario['match']}</span>
  <span class="badge">Minute {scenario['minute']}</span>
  <span class="badge">{scenario['category'].replace('_',' ').title()}</span>
  <p style="margin-top:1rem">{scenario['description']}</p>
</div>
""", unsafe_allow_html=True)

lc, rc = st.columns(2)

with lc:
    law = scenario['relevant_law']
    st.markdown(f"""
    <div class="law-box">
      <b>⚖️ Law {law['law_number']}: {law['law_title']}</b><br>
      <span style="color:#a8a8a8">{law['excerpt']}</span><br>
      <span style="font-size:0.75rem;color:#666">Source: 2025/26 IFAB Laws of the Game, p.{law['source_page']}</span>
    </div>
    """, unsafe_allow_html=True)

    if scenario.get('historical_overturn_rate') is not None:
        rate = scenario['historical_overturn_rate']
        st.metric(
            f"Historical overturn rate — {scenario['category'].replace('_',' ')} reviews",
            f"{rate:.0%}",
            help=scenario.get('overturn_rate_source', '')
        )
    else:
        st.info(f"📋 Overturn rate for this category:\n\n{scenario.get('overturn_rate_source', 'See official FIFA technical report')}")

with rc:
    st.markdown("#### 🚫 What this system cannot know")
    st.markdown("""
    <div class="unknown-box">
    These factors are real and material — they simply aren't in any structured dataset:
    </div>""", unsafe_allow_html=True)
    for item in scenario['what_the_model_does_not_know']:
        st.markdown(f"- {item}")

    st.markdown("#### 🏛️ The VAR protocol principle at stake")
    if scenario['category'] == 'penalty':
        st.markdown("""
        VAR corrects **clear and obvious errors** only. When a referee makes an on-field
        penalty decision and there is contact, the VAR threshold is deliberately high —
        the system is designed to preserve on-field authority. Most checked penalty
        decisions in 2022 **were** overturned (5/9), but that reflects that VAR was
        mostly called on clear misses, not close calls.
        """)
    elif scenario['category'] == 'goal_line':
        st.markdown("""
        Goal-line decisions use a dedicated camera system separate from the main VAR
        feed. The decision is binary — any part of the ball must have fully crossed
        the line for the goal to be disallowed. The camera frame rate and angle
        actually used by officials is often different from the broadcast angle viewers see.
        """)
    else:
        st.markdown("""
        Each VAR category has its own review threshold and camera protocol. Context matters —
        the same contact in a group stage match vs a final may be evaluated identically
        under the Laws, but the scrutiny applied (and the public reaction) differs enormously.
        """)

st.markdown("---")
st.markdown("### 💬 Ask Granite about this incident")
st.caption("Switch to the Granite Chat page to get IBM AI narration grounded in the data shown above.")
if st.button("→ Open Granite Chat with this scenario loaded"):
    st.session_state['preloaded_scenario'] = scenario
    st.switch_page("pages/4_Granite_Chat.py")
