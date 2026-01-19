import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="IBEX Оптимизатор", layout="wide")

st.title("⚡ IBEX Оптимизатор за Експорт")

# -----------------------------
# SESSION STATE – DEFAULT VALUES
# -----------------------------
if "period_length" not in st.session_state:
    st.session_state.period_length = 60   # минути

if "num_periods" not in st.session_state:
    st.session_state.num_periods = 3      # брой периоди

# -----------------------------
# ИЗБОР НА ДЪЛЖИНА НА ПЕРИОДА
# -----------------------------
st.subheader("Дължина на периода")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("30 мин"):
        st.session_state.period_length = 30

with colB:
    if st.button("60 мин"):
        st.session_state.period_length = 60

with colC:
    if st.button("120 мин"):
        st.session_state.period_length = 120

st.write(f"Избрана дължина: **{st.session_state.period_length} минути**")

# -----------------------------
# ИЗБОР НА БРОЙ ПЕРИОДИ (1–5)
# -----------------------------
st.subheader("Брой периоди")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    if st.button("1 период"):
        st.session_state.num_periods = 1

with c2:
    if st.button("2 периода"):
        st.session_state.num_periods = 2

with c3:
    if st.button("3 периода"):
        st.session_state.num_periods = 3

with c4:
    if st.button("4 периода"):
        st.session_state.num_periods = 4

with c5:
    if st.button("5 периода"):
        st.session_state.num_periods = 5

st.write(f"Избрани периоди: **{st.session_state.num_periods}**")

# -----------------------------
# КАЧВАНЕ НА ФАЙЛ
# -----------------------------
st.subheader("Качи IBEX CSV файл")
uploaded_file = st.file_uploader("Избери файл", type=["csv"])

# -----------------------------
# БУТОН ИЗЧИСЛИ
# -----------------------------
if st.button("Изчисли"):

    if uploaded_file is None:
        st.error("Моля, качи CSV файл.")
        st.stop()

    df = pd.read_csv(uploaded_file)

    # Очакваме колоните да са: Time, Price
    df["Time"] = pd.to_datetime(df["Time"])
    df = df.sort_values("Time")

    period_minutes = st.session_state.period_length
    num_periods = st.session_state.num_periods

    # Създаваме периоди
    results = []
    for i in range(num_periods):
        start = df["Time"].min() + pd.Timedelta(minutes=i * period_minutes)
        end = start + pd.Timedelta(minutes=period_minutes)

        mask = (df["Time"] >= start) & (df["Time"] < end)
        subset = df[mask]

        if len(subset) > 0:
            avg_price = subset["Price"].mean()
        else:
            avg_price = np.nan

        results.append({
            "Период": i + 1,
            "Начало": start,
            "Край": end,
            "Средна цена": round(avg_price, 2)
        })

    result_df = pd.DataFrame(results)

    st.subheader("График за действие")
    st.dataframe(result_df, use_container_width=True)
