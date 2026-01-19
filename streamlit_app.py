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
# Бутоните за избор на 1, 2 или 3 периода
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

with col3:
    if st.button("3 периода"):
        st.session_state.num_periods = 3

st.write(f"Избрани периоди: **{st.session_state.num_periods}**")

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

def duration_str(start, end):
    t1 = datetime.strptime(start, "%H:%M")
    t2 = datetime.strptime(end, "%H:%M")
    diff = t2 - t1
    minutes = diff.seconds // 60
    h = minutes // 60
    m = minutes % 60

    if h > 0 and m > 0:
        return f"{h}ч {m}м"
    elif h > 0:
        return f"{h}ч"
    else:
        return f"{m}м"

def generate_length_combinations(total, num_parts):
    results = []

    def backtrack(remaining, parts_left, current):
        if parts_left == 0:
            if remaining == 0:
                results.append(current)
            return

        for x in range(1, remaining - parts_left + 2):
            backtrack(remaining - x, parts_left - 1, current + [x])

    backtrack(total, num_parts, [])
    return results

def best_positions_for_lengths(prices, lengths, total_qh):
    n = len(prices)
    k = len(lengths)
    best_avg = -1
    best_periods = None

    for starts in itertools.combinations(range(n), k):
        valid = True
        periods = []
        last_end = -1

        for start, length in zip(starts, lengths):
            end = start + length
            if start <= last_end or end > n:
                valid = False
                break
            periods.append((start, end))
            last_end = end

        if not valid:
            continue

        total_sum = sum(np.sum(prices[s:e]) for s, e in periods)
        avg = total_sum / total_qh

        if avg > best_avg:
            best_avg = avg
            best_periods = periods

    return best_periods, best_avg

def find_best_periods(prices, total_qh, num_periods):
    best_avg = -1
    best_periods = None

    combos = generate_length_combinations(total_qh, num_periods)

    for lengths in combos:
        periods, avg = best_positions_for_lengths(prices, lengths, total_qh)
        if periods is not None and avg > best_avg:
            best_avg = avg
            best_periods = periods

    return best_periods, best_avg

def format_periods(periods, df):
    output = []
    for i, (s, e) in enumerate(periods, start=1):
        start_time = df.loc[s, "Период на доставка"].split("-")[0].strip()
        end_time = df.loc[e - 1, "Период на доставка"].split("-")[1].strip()
        dur = duration_str(start_time, end_time)
        output.append(f"Период {i}: {start_time} – {end_time} ({dur})")
    return "\n".join(output)

# ---------------------------------------------------------
# Бутон за изчисление
# ---------------------------------------------------------
if uploaded_file is not None and st.button("Изчисли"):

    try:
        ext = os.path.splitext(uploaded_file.name)[1].lower()

        if ext in ['.csv', '.txt']:
            df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        elif ext == '.xls':
            df = pd.read_excel(uploaded_file, skiprows=9, engine='xlrd')
        elif ext == '.xlsx':
            df = pd.read_excel(uploaded_file, skiprows=9, engine='openpyxl')
        else:
            st.error("Неподдържан файлов формат.")
            st.stop()

        df.columns = [c.strip() for c in df.columns]
        df = df[df['Продукт'].astype(str).str.startswith('QH')].copy()

        if df['Цена (EUR/MWh)'].dtype == object:
            df['Цена (EUR/MWh)'] = (
                df['Цена (EUR/MWh)']
                .astype(str)
                .str.replace(',', '.')
                .astype(float)
            )

        df['QH'] = df['Продукт'].str.extract(r'QH\s*(\d+)').astype(int)
        df = df.sort_values('QH').reset_index(drop=True)

        prices = df['Цена (EUR/MWh)'].to_numpy()

        periods, avg_price = find_best_periods(
            prices,
            total_qh,
            st.session_state.num_periods
        )

        st.subheader("⏳ Най-добър вариант:")
        st.text(format_periods(periods, df))
        st.success(f"Обща средна цена: {avg_price:.2f} EUR/MWh")

        # ---------------------------------------------------------
        # Таблица: Продавай / Не продавай
        # ---------------------------------------------------------
        selected_qh = set()
        for s, e in periods:
            selected_qh.update(range(s, e))

        table_rows = []
        current_status = None
        start_idx = None

        for i in range(len(prices)):
            status = "Продавай" if i in selected_qh else "Не продавай"

            if status != current_status:
                if current_status is not None:
                    raw_start = df.loc[start_idx, "Период на доставка"].split("-")[0].strip()
                    raw_end = df.loc[i - 1, "Период на доставка"].split("-")[1].strip()

                    start_time = add_one_hour(raw_start)
                    end_time = add_one_hour(raw_end)

                    avg_block = df.loc[start_idx:i - 1, "Цена (EUR/MWh)"].mean()
                    table_rows.append((start_time, end_time, current_status, avg_block))

                current_status = status
                start_idx = i

        if current_status is not None:
            raw_start = df.loc[start_idx, "Период на доставка"].split("-")[0].strip()
            raw_end = df.loc[len(prices) - 1, "Период на доставка"].split("-")[1].strip()

            start_time = add_one_hour(raw_start)
            end_time = add_one_hour(raw_end)

            avg_block = df.loc[start_idx:len(prices) - 1, "Цена (EUR/MWh)"].mean()
            table_rows.append((start_time, end_time, current_status, avg_block))

        period_numbers = [str(i + 1) for i in range(len(table_rows))]
        table_df = pd.DataFrame(table_rows, columns=["Start Time", "End Time", "Действие", "Средна цена"])
        table_df.insert(0, "Период", period_numbers)

        def highlight_sell_row(row):
            if row["Действие"] == "Продавай":
                return ["background-color: #d4f8d4; font-weight: bold;"] * len(row)
            return [""] * len(row)

        styled_df = table_df.style.apply(highlight_sell_row, axis=1)

        st.subheader("📋 График за действие")
        st.dataframe(styled_df, use_container_width=True)

        st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Грешка: {e}")
