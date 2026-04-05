import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="IBEX BG Оптимизатор", layout="centered")

st.title("💰 Смарт Стратегия (Българско време)")

# 1. Настройки
col1, col2 = st.columns(2)
with col1:
    total_needed_qh = st.slider("Общо QH за работа:", 1, 96, 12)
with col2:
    num_blocks = st.radio("Раздели на брой блокове:", [1, 2, 3], index=0)

uploaded_file = st.file_uploader("Зареди файл", type=['csv', 'txt'])

def adjust_time(time_str):
    """Добавя 1 час към часа от файла (CET -> EET)"""
    try:
        t = datetime.strptime(time_str.strip(), "%H:%M")
        t_new = t + timedelta(hours=1)
        return t_new.strftime("%H:%M")
    except:
        return time_str

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].astype(str).str.replace(',', '.').astype(float)
        prices = df['Цена (EUR/MWh)'].values

        # 2. Алгоритъм за намиране на най-добрите блокове
        best_avg = -1
        best_combination = []

        if num_blocks == 1:
            for i in range(len(prices) - total_needed_qh + 1):
                current_avg = np.mean(prices[i : i + total_needed_qh])
                if current_avg > best_avg:
                    best_avg = current_avg
                    best_combination = [(i, i + total_needed_qh - 1)]

        elif num_blocks == 2:
            for len1 in range(1, total_needed_qh):
                len2 = total_needed_qh - len1
                for i in range(len(prices) - len1 - len2):
                    sum1 = np.sum(prices[i : i + len1])
                    for j in range(i + len1 + 1, len(prices) - len2 + 1):
                        sum2 = np.sum(prices[j : j + len2])
                        combined_avg = (sum1 + sum2) / total_needed_qh
                        if combined_avg > best_avg:
                            best_avg = combined_avg
                            best_combination = [(i, i + len1 - 1), (j, j + len2 - 1)]

        elif num_blocks == 3:
            for len1 in range(1, total_needed_qh - 1):
                for len2 in range(1, total_needed_qh - len1):
                    len3 = total_needed_qh - len1 - len2
                    for i in range(len(prices) - len1 - len2 - len3):
                        s1 = np.sum(prices[i : i + len1])
                        for j in range(i + len1 + 1, len(prices) - len2 - len3):
                            s2 = np.sum(prices[j : j + len2])
                            for k in range(j + len2 + 1, len(prices) - len3 + 1):
                                s3 = np.sum(prices[k : k + len3])
                                combined_avg = (s1 + s2 + s3) / total_needed_qh
                                if combined_avg > best_avg:
                                    best_avg = combined_avg
                                    best_combination = [(i, i + len1 - 1), (j, j + len2 - 1), (k, k + len3 - 1)]

        # 3. Показване на резултатите с коригирано време
        st.subheader("📅 План за работа (Българско време):")
        
        for idx, (b_start, b_end) in enumerate(best_combination):
            # Вземаме часовете и добавяме +1 час
            raw_start = df.loc[b_start, 'Период на доставка'].split('-')[0]
            raw_end = df.loc[b_end, 'Период на доставка'].split('-')[1]
            
            start_t = adjust_time(raw_start)
            end_t = adjust_time(raw_end)
            avg_p = df.loc[b_start:b_end, 'Цена (EUR/MWh)'].mean()
            
            st.success(f"🟢 **ПРОДАВАЙ: {start_t} - {end_t}** | Средна: **{avg_p:.2f} EUR**")
            
            if idx < len(best_combination) - 1:
                pause_raw_start = df.loc[b_end, 'Период на доставка'].split('-')[1]
                pause_raw_end = df.loc[best_combination[idx+1][0], 'Период на доставка'].split('-')[0]
                
                p_start = adjust_time(pause_raw_start)
                p_end = adjust_time(pause_raw_end)
                p_avg = df.loc[b_end+1 : best_combination[idx+1][0]-1, 'Цена (EUR/MWh)'].mean()
                st.error(f"🔴 **НЕ ПРОДАВАЙ: {p_start} - {p_end}** | Средна: **{p_avg:.2f} EUR**")

        st.metric("Обща средна цена (EET Time)", f"{best_avg:.2f} EUR")

    except Exception as e:
        st.error(f"Грешка: {e}")
