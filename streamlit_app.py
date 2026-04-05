import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("💰 Смарт Стратегия")

# 1. Настройки
col1, col2 = st.columns(2)
with col1:
    total_needed_qh = st.slider("Общо QH за работа:", 1, 96, 12)
with col2:
    num_blocks = st.radio("Раздели на брой блокове:", [1, 2, 3], index=0)

uploaded_file = st.file_uploader("Зареди файл", type=['csv', 'txt'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].astype(str).str.replace(',', '.').astype(float)
        prices = df['Цена (EUR/MWh)'].values

        # 2. Алгоритъм за намиране на N най-добри блока с фиксирана обща дължина
        best_avg = -1
        best_combination = []

        if num_blocks == 1:
            # Търсим един непрекъснат блок с дължина total_needed_qh
            for i in range(len(prices) - total_needed_qh + 1):
                current_avg = np.mean(prices[i : i + total_needed_qh])
                if current_avg > best_avg:
                    best_avg = current_avg
                    best_combination = [(i, i + total_needed_qh - 1)]

        elif num_blocks == 2:
            # Разделяме total_needed_qh на две части (len1 + len2 = total_needed_qh)
            for len1 in range(1, total_needed_qh):
                len2 = total_needed_qh - len1
                for i in range(len(prices) - len1 - len2):
                    avg1 = np.mean(prices[i : i + len1])
                    for j in range(i + len1 + 1, len(prices) - len2 + 1):
                        avg2 = np.mean(prices[j : j + len2])
                        combined_avg = (avg1 * len1 + avg2 * len2) / total_needed_qh
                        if combined_avg > best_avg:
                            best_avg = combined_avg
                            best_combination = [(i, i + len1 - 1), (j, j + len2 - 1)]

        elif num_blocks == 3:
            # Разделяме на три части (len1 + len2 + len3 = total_needed_qh)
            # За по-бърза работа оптимизираме търсенето
            for len1 in range(1, total_needed_qh - 1):
                for len2 in range(1, total_needed_qh - len1):
                    len3 = total_needed_qh - len1 - len2
                    for i in range(len(prices) - len1 - len2 - len3):
                        val1 = np.sum(prices[i : i + len1])
                        for j in range(i + len1 + 1, len(prices) - len2 - len3):
                            val2 = np.sum(prices[j : j + len2])
                            for k in range(j + len2 + 1, len(prices) - len3 + 1):
                                val3 = np.sum(prices[k : k + len3])
                                combined_avg = (val1 + val2 + val3) / total_needed_qh
                                if combined_avg > best_avg:
                                    best_avg = combined_avg
                                    best_combination = [(i, i + len1 - 1), (j, j + len2 - 1), (k, k + len3 - 1)]

        # 3. Показване на резултатите
        st.subheader("📅 План за максимална печалба:")
        
        for idx, (b_start, b_end) in enumerate(best_combination):
            start_t = df.loc[b_start, 'Период на доставка'].split('-')[0]
            end_t = df.loc[b_end, 'Период на доставка'].split('-')[1]
            avg_p = df.loc[b_start:b_end, 'Цена (EUR/MWh)'].mean()
            
            st.success(f"🟢 **ПРОДАВАЙ: {start_t} - {end_t}** | Средна: **{avg_p:.2f} EUR**")
            
            if idx < len(best_combination) - 1:
                p_start = df.loc[b_end, 'Период на доставка'].split('-')[1]
                p_end = df.loc[best_combination[idx+1][0], 'Период на доставка'].split('-')[0]
                p_avg = df.loc[b_end+1 : best_combination[idx+1][0]-1, 'Цена (EUR/MWh)'].mean()
                st.error(f"🔴 **НЕ ПРОДАВАЙ: {p_start} - {p_end}** | Средна: **{p_avg:.2f} EUR**")

        st.metric("Обща средна цена за всички работни QH", f"{best_avg:.2f} EUR")

    except Exception as e:
        st.error(f"Грешка: {e}")
