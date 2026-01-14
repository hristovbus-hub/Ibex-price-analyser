import streamlit as st
import pandas as pd
from itertools import combinations

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")
st.title("📊 Оптимизатор – Топ 3 периода (общо 3 часа)")

uploaded_file = st.file_uploader("Качи DAM CSV файл", type=['csv', 'txt'])

def qh_to_time(qh):
    minutes = (qh - 1) * 15
    h = minutes // 60
    m = minutes % 60
    return f"{h:02d}:{m:02d}"

def interval_to_time(start, end):
    return qh_to_time(start), qh_to_time(end + 1)

def load_prices(uploaded_file):
    df = pd.read_csv(uploaded_file, sep=";", skiprows=9)
    df.columns = [c.strip() for c in df.columns]

    df["Цена (EUR/MWh)"] = (
        df["Цена (EUR/MWh)"]
        .astype(str)
        .str.replace(",", ".")
        .astype(float)
    )

    df["QH"] = df["Продукт"].str.replace("QH", "").astype(int)
    df = df[["QH", "Период на доставка", "Цена (EUR/MWh)"]]
    df = df.set_index("QH")
    return df

def all_intervals(prices):
    intervals = []
    qhs = sorted(prices.index)

    for start in qhs:
        for end in qhs:
            if end >= start:
                interval = list(range(start, end + 1))
                avg_price = prices.loc[interval, "Цена (EUR/MWh)"].mean()
                intervals.append((start, end, len(interval), avg_price))
    return intervals

def find_best_three(intervals):
    best = None

    for a, b, c in combinations(intervals, 3):
        total_len = a[2] + b[2] + c[2]
        if total_len != 12:
            continue

        # Проверка за застъпване
        if not (a[1] < b[0] or b[1] < a[0]):
            continue
        if not (a[1] < c[0] or c[1] < a[0]):
            continue
        if not (b[1] < c[0] or c[1] < b[0]):
            continue

        total_avg = (
            a[3] * a[2] +
            b[3] * b[2] +
            c[3] * c[2]
        ) / 12

        if best is None or total_avg > best[0]:
            best = (total_avg, a, b, c)

    return best

if uploaded_file:
    try:
        df = load_prices(uploaded_file)
        intervals = all_intervals(df)
        best = find_best_three(intervals)

        if best is None:
            st.error("Не е намерена комбинация от 3 периода с общо 12 QH.")
            st.stop()

        total_avg, a, b, c = best

        st.subheader(f"📈 Обща средна цена: **{total_avg:.2f} EUR/MWh**")

        for idx, interval in enumerate([a, b, c], start=1):
            start, end, length, avg = interval
            start_time, end_time = interval_to_time(start, end)

            st.warning(
                f"🔹 Период {idx}: **{start_time} – {end_time}** "
                f"({length} QH) | Средна: **{avg:.2f} EUR/MWh**"
            )

        st.line_chart(df["Цена (EUR/MWh)"])

    except Exception as e:
        st.error(f"Грешка: {e}")
