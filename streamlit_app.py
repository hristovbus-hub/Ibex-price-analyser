import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title="IBEX BG Оптимизатор", layout="centered")

st.title("💰 Смарт Стратегия с Филтър")

# 1. Настройки
col1, col2 = st.columns(2)
with col1:
    total_needed_qh = st.slider("Общо QH за работа:", 1, 48, 12)
with col2:
    num_blocks = st.radio("Раздели на брой блокове:", [1, 2, 3], index=0)

# НОВО: Избор на часови диапазон
time_filter = st.radio("Период от деня (БГ време):", ["Цял ден", "Сутрин (01:00 - 12:00)", "Следобед (12:00 - 01:00)"], horizontal=True)

uploaded_file = st.file_uploader("Зареди файл", type=['csv', 'txt'])

def adjust_time(time_str):
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
        
        # Добавяме колона за Българско време за филтриране
        df['BG_Start'] = df['Период на доставка'].str.split('-').str[0].apply(adjust_time)
        df['BG_Hour'] = df['BG_Start'].str.split(':').str[0].astype(int)

        # Прилагане на филтъра
        if time_filter == "Сутрин (01:00 - 12:00)":
            work_df = df[(df['BG_Hour'] >= 1) & (df['BG_Hour'] < 12)].copy()
        elif time_filter == "Следобед (12:00 - 01:00)":
            # Включва от 12 на обяд до полунощ (23:45)
            work_df = df[(df['BG_Hour'] >= 12) | (df['BG_Hour'] == 0)].copy()
        else:
            work_df = df.copy()

        prices = work_df['Цена (EUR/MWh)'].values
        indices = work_df.index.values

        if len(prices) < total_needed_qh:
            st.warning(f"В избрания период има само {len(prices)} налични интервала. Намали QH или промени филтъра.")
        else:
            # 2. Алгоритъм (използваме work_df)
            best_avg = -1
            best_combination = []

            # (Логиката за 1, 2 и 3 блока остава същата, но работи върху филтрираните данни)
            if num_blocks == 1:
                for i in range(len(prices) - total_needed_qh + 1):
                    current_avg = np.mean(prices[i : i + total_needed_qh])
                    if current_avg > best_avg:
                        best_avg = current_avg
                        best_combination = [(indices[i], indices[i + total_needed_qh - 1])]

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
                                best_combination = [(indices[i], indices[i + len1 - 1]), (indices[j], indices[j + len2 - 1])]

            elif num_blocks == 3:
                # Оптимизирано за 3 блока върху филтрирани данни
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
                                        best_combination = [(indices[i], indices[i + len1 - 1]), (indices[j], indices[j + len2 - 1]), (indices[k], indices[k + len3 - 1])]

            # 3. Показване
            st.subheader(f"📅 План за {time_filter}:")
            for idx, (b_start, b_end) in enumerate(best_combination):
                start_t = adjust_time(df.loc[b_start, 'Период на доставка'].split('-')[0])
                end_t = adjust_time(df.loc[b_end, 'Период на доставка'].split('-')[1])
                avg_p = df.loc[b_start:b_end, 'Цена (EUR/MWh)'].mean()
                st.success(f"🟢 **ПРОДАВАЙ: {start_t} - {end_t}** | Средна: **{avg_p:.2f} EUR**")
                
                if idx < len(best_combination) - 1:
                    p_start = adjust_time(df.loc[b_end, 'Период на доставка'].split('-')[1])
                    p_end = adjust_time(df.loc[best_combination[idx+1][0], 'Период на доставка'].split('-')[0])
                    p_avg = df.loc[b_end+1 : best_combination[idx+1][0]-1, 'Цена (EUR/MWh)'].mean()
                    st.error(f"🔴 **НЕ ПРОДАВАЙ: {p_start} - {p_end}** | Средна: **{p_avg:.2f} EUR**")

            st.metric("Максимална средна цена за периода", f"{best_avg:.2f} EUR")

    except Exception as e:
        st.error(f"Грешка: {e}")
