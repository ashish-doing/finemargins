"""
app/data_loader.py
Single source of data loading for all pages. Streamlit caches everything.
"""
import streamlit as st
import pandas as pd
import json
import pickle
from pathlib import Path

BASE = Path(__file__).parent.parent

@st.cache_data
def load_penalties():
    return pd.read_parquet(BASE / "data/processed/penalty_shap.parquet")

@st.cache_data
def load_late_shots():
    return pd.read_parquet(BASE / "data/processed/late_shot_probs.parquet")

@st.cache_data
def load_player_profiles():
    return pd.read_parquet(BASE / "data/processed/player_profiles.parquet")

@st.cache_data
def load_metrics():
    with open(BASE / "pipeline/model_artifacts/metrics.json") as f:
        return json.load(f)

@st.cache_resource
def load_models():
    with open(BASE / "pipeline/model_artifacts/models.pkl", "rb") as f:
        return pickle.load(f)

@st.cache_data
def load_scenarios():
    with open(BASE / "ibm_layer/officiating_scenarios.json") as f:
        return json.load(f)
