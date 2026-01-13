import streamlit as st
import pandas as pd

st.set_page_config(page_title="IBEX Максимум", layout="centered")

st.title("📊 Резултати по блокове (359.84)")
st.write("Търсене на 12-те най-скъпи интервала за деня.")

uploaded_file = st.file_uploader("Избери файл", type=['csv', 'txt'])

if uploaded_file is not None:
    try:
        # Четем файла, като изчистваме заглавията
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        
        # Превръщаме цената в число и чистим интервалите
        if df['Цена (EUR/MWh)'].dtype == object:
            df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].str.replace(',', '.').astype(float)

        # 1. ТУК Е КЛЮЧЪТ: Избираме ТОЧНО 12-те най-високи цени за целия ден
        top_12 = df.nlargest(12, 'Цена (EUR/MWh)').sort_index()

        # 2. Логика за групиране в блокове
        blocks = []
        if not top_12.empty:
            start_idx = top_12.index[0]
            last_idx = start_idx
            
            for i in range(1, len(top_12)):
                current_idx = top_12.index[i]
                if current_idx == last_idx + 1:
                    last_idx = current_idx
                else:
                    s_time = df.loc[start_idx, 'Период на доставка'].split('-')[0]
                    e_time = df.loc[last_idx, 'Период на доставка'].split('-')[1]
                    avg_p = df.loc[start_idx:last_idx, 'Цена (EUR/MWh)'].mean()
                    blocks.append((s_time, e_time, avg_p))
                    start_idx = current_idx
                    last_idx = current_idx
            
            # Добавяне на финалния блок
            s_time = df.loc[start_idx, 'Период на доставка'].split('-')[0]
            e_time = df.loc[last_idx, 'Период на доставка'].split('-')[1]
            avg_p = df.loc[start_idx:last_idx, 'Цена (EUR/MWh)'].mean()
            blocks.append((s_time, e_time, avg_p))

        # 3. Резултати
        st.subheader("⏳ Периоди с най-висока цена:")
        for b_start, b_end, b_avg in blocks:
            st.warning(f"🕒 **{b_start} - {b_end}** | Средна: **{b_avg:.2f} EUR**")

        total_avg = top_12['Цена (EUR/MWh)'].mean()
        st.success(f"📈 ОБЩА СРЕДНА ЦЕНА (3ч): **{total_avg:.2f} EUR**")
        
        # Графика
        st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Грешка: {e}")
        
