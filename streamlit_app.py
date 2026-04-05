import streamlit as st
import pandas as pd

st.set_page_config(page_title="IBEX Търговски Помощник", layout="centered")

st.title("💰 Стратегия за Продажба")

# 1. Настройки на стратегията
col1, col2 = st.columns(2)
with col1:
    total_qh = st.slider("Общо QH за деня:", 1, 20, 12)
with col2:
    num_periods = st.radio("Брой периоди на продажба:", [1, 2, 3], index=2)

uploaded_file = st.file_uploader("Зареди файл с цени", type=['csv', 'txt'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].astype(str).str.replace(',', '.').astype(float)

        # Намираме най-добрите интервали
        top_indices = df.nlargest(total_qh, 'Цена (EUR/MWh)').index.sort_values()
        
        blocks = []
        if len(top_indices) > 0:
            start_idx = top_indices[0]
            last_idx = start_idx
            for i in range(1, len(top_indices)):
                if top_indices[i] == last_idx + 1:
                    last_idx = top_indices[i]
                else:
                    blocks.append((start_idx, last_idx))
                    start_idx = top_indices[i]
                    last_idx = start_idx
            blocks.append((start_idx, last_idx))

        # Ограничаваме до избрания брой периоди
        blocks = sorted(blocks, key=lambda x: df.loc[x[0]:x[1], 'Цена (EUR/MWh)'].mean(), reverse=True)[:num_periods]
        blocks.sort(key=lambda x: x[0]) 

        st.subheader("📅 План за деня:")
        
        for i in range(len(blocks)):
            b_start, b_end = blocks[i]
            start_time = df.loc[b_start, 'Период на доставка'].split('-')[0]
            end_time = df.loc[b_end, 'Период на доставка'].split('-')[1]
            avg_p = df.loc[b_start:b_end, 'Цена (EUR/MWh)'].mean()

            # ЗЕЛЕНО: ПРОДАВАЙ
            st.success(f"🟢 **ПРОДАВАЙ: {start_time} - {end_time}** | Цена: **{avg_p:.2f} EUR**")

            # ЧЕРВЕНО: НЕ ПРОДАВАЙ (със средна цена)
            if i < len(blocks) - 1:
                next_start_idx = blocks[i+1][0]
                pause_idx_start = b_end + 1
                pause_idx_end = next_start_idx - 1
                
                if pause_idx_start <= pause_idx_end:
                    pause_start = df.loc[b_end, 'Период на доставка'].split('-')[1]
                    pause_end = df.loc[next_start_idx, 'Период на доставка'].split('-')[0]
                    # Изчисляваме средната цена за периода "Не продавай"
                    pause_avg_p = df.loc[pause_idx_start:pause_idx_end, 'Цена (EUR/MWh)'].mean()
                    st.error(f"🔴 **НЕ ПРОДАВАЙ: {pause_start} - {pause_end}** | Цена: **{pause_avg_p:.2f} EUR**")

        if blocks:
            total_avg = sum(df.loc[b[0]:b[1], 'Цена (EUR/MWh)'].mean() for b in blocks) / len(blocks)
            st.metric("Средна цена на продажба", f"{total_avg:.2f} EUR")

    except Exception as e:
        st.error(f"Грешка: {e}")
        
