import streamlit as st
import pandas as pd

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Резултати по блокове")
st.write("Най-скъпите 3 часа, групирани по периоди.")

uploaded_file = st.file_uploader("Избери файл", type=['csv', 'txt'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        if df['Цена (EUR/MWh)'].dtype == object:
            df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].str.replace(',', '.').astype(float)

        # 1. Намираме 12-те най-скъпи интервала
        top_12 = df.nlargest(12, 'Цена (EUR/MWh)').sort_index()

        # 2. Логика за групиране на съседни интервали
        blocks = []
        if not top_12.empty:
            start_idx = top_12.index[0]
            current_idx = start_idx
            
            for i in range(1, len(top_12)):
                if top_12.index[i] == current_idx + 1:
                    current_idx = top_12.index[i]
                else:
                    # Затваряме текущия блок и започваме нов
                    start_time = df.loc[start_idx, 'Период на доставка'].split('-')[0]
                    end_time = df.loc[current_idx, 'Период на доставка'].split('-')[1]
                    avg_price = df.loc[start_idx:current_idx, 'Цена (EUR/MWh)'].mean()
                    blocks.append((start_time, end_time, avg_price))
                    
                    start_idx = top_12.index[i]
                    current_idx = start_idx
            
            # Добавяме последния блок
            start_time = df.loc[start_idx, 'Период на доставка'].split('-')[0]
            end_time = df.loc[current_idx, 'Период на доставка'].split('-')[1]
            avg_price = df.loc[start_idx:current_idx, 'Цена (EUR/MWh)'].mean()
            blocks.append((start_time, end_time, avg_price))

        # 3. Показване на резултатите
        st.subheader("⏳ Периоди за работа:")
        for b_start, b_end, b_avg in blocks:
            st.warning(f"🕒 **{b_start} - {b_end}** | Средна цена: **{b_avg:.2f} EUR**")

        total_avg = top_12['Цена (EUR/MWh)'].mean()
        st.success(f"📈 ОБЩА СРЕДНА ЦЕНА (3ч): **{total_avg:.2f} EUR**")
        
        st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Грешка: {e}")
