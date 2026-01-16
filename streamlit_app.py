import streamlit as st
import pandas as pd
import numpy as np
import itertools
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Резултати по блокове")
st.write("Избери общата дължина (в QH) и изчисли най-добрите периоди.")

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
# Качване на файл
# ---------------------------------------------------------
uploaded_file = st.file_uploader(
    "Избери файл",
    type=['csv', 'txt', 'xls', 'xlsx'],
    accept_multiple_files=False
)

# ---------------------------------------------------------
# Функции
# ---------------------------------------------------------
def add_one_hour(time_str):
    t = datetime.strptime(time_str, "%H:%M")
    t += timedelta(hours=1)
    return t.strftime("%H:%M")

def generate_length_combinations(total):
    combos = [[total]]
    for a in range(1, total):
        combos.append([a, total - a])
    for a in range(1, total - 1):
        for b in range(1, total - a):
            c = total - a - b
            combos.append([a, b, c])
    return combos

def best_positions_for_lengths(prices, lengths):
    n = len(prices)
   
