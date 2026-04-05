import streamlit as st
import pandas as pd

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Професионален Анализ")

# Настройки от потребителя
qh_count = st.slider("Обща дължина (в QH):", min_value=1, max_value=96, value=12)
st.info(f"Търсим най-добрите {qh_count} интервала (общо {qh_count*15} минути)")

uploaded_file = st.file_uploader("Избери файл", type=['csv', 'txt'])

if uploaded_file is not None:
    try:
        # Четем файла внимателно
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        
        # Пречистване на цената - решаваме проблема 'int' and 'str'
        if 'Цена (EUR/MWh)' in df.columns:
            df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].astype(str).str.replace(',', '.')
            df['Цена (EUR/MWh)'] = pd.to_numeric(df['Цена (EUR/MWh)'], errors='coerce')
            df = df.dropna(subset=['Цена (EUR/MWh)']) # Махаме празни редове

        # 1. Намираме най-високите интервали според избора от слайдера
        top_n = df.nlargest(qh_count, 'Цена (EUR/MWh)').sort_index()

        # 2. Групиране в логически блокове
        blocks = []
        if not top_n.empty:
            start_idx = top_n.index[0]
            last_idx = start_idx
            
            for i in range(1, len(top_n)):
                current_idx = top_n.index[i]
                if current_idx == last_idx + 1:
                    last_idx = current_idx
                else:
                    s_time = str(df.loc[start_idx, 'Период на доставка']).split('-')[0]
                    e_time = str(df.loc[last_idx, 'Период на доставка']).split('-')[1]
                    avg_p = df.loc[start_idx:last_idx, 'Цена (EUR/MWh)'].mean()
                    blocks.append((s_time, e_time, avg_p))
                    start_idx = current_idx
                    last_idx = current_idx
            
            # Последен блок
            s_time = str(df.loc[start_idx, 'Период на доставка']).split('-')[0]
            e_time = str(df.loc[last_idx, 'Период на доставка']).split('-')[1]
            avg_p = df.loc[start_idx:last_idx, 'Цена (EUR/MWh)'].mean()
            blocks.append((s_time, e_time, avg_p))

        # 3. Показване на резултатите
        st.subheader("⏳ Резултати по периоди:")
        for b_start, b_end, b_avg in blocks:
            st.warning(f"🕒 **{b_start} - {b_end}** | Средна цена: **{b_avg:.2f} EUR**")

        total_avg = top_n['Цена (EUR/MWh)'].mean()
        st.success(f"📈 МАКСИМАЛНА СРЕДНА ЦЕНА: **{total_avg:.2f} EUR**")
        
        # Графика
        st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Възникна грешка при обработката: {e}")
                
