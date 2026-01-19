import streamlit as st
import pandas as pd
import numpy as np
import itertools
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Резултати по блокове")
st.write("Избери общата дължина (в QH), броя периоди и изчисли най-добрите блокове.")

# ---------------------------------------------------------
# Плъзгач за избор на обща дължина
# ---------------------------------------------------------
total_qh = st.slider(
    "Обща дължина (в QH):",
    min_value=1,
    max_value=20,
    value=11,
    step=1
)

# ---------------------------------------------------------
# Избор на брой периоди (1–3)
# ---------------------------------------------------------
st.subheader("Брой периоди")

col1, col2, col3 = st.columns(3)

if "num_periods" not in st.session_state:
    st.session_state.num_periods = 1  # по подразбиране

with col1:
    if st.button("1 период"):
        st.session_state.num_periods = 1

with col2:
    if st.button("2 периода"):
        st.session_state.num_periods = 2
