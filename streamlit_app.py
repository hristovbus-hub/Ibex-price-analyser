import streamlit as st
import pandas as pd

st.set_page_config(page_title="Максимален Анализатор", layout="centered")

st.title("🚀 Топ 12 Интервала (Хронологично)")
st.write("Приложението избира 12-те най-скъпи момента и ги подрежда по време.")

uploaded_file = st.file_uploader("Избери файл", type=['csv', 'txt'])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        
        if df['Цена (EUR/MWh)'].dtype == object:
            df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].str.replace(',', '.').astype(float)

        # 1. Намираме 12-те най-скъпи интервала
        # Използваме nlargest, за да вземем най-високите стойности
        top_12 = df.nlargest(12, 'Цена (EUR/MWh)')

        # 2. ТУК Е ПРОМЯНАТА: Подреждаме ги по оригиналния ред (време)
        top_12_chronological = top_12.sort_index()

        st.subheader("📅 Твоят график за деня:")
        
        for index, row in top_12_chronological.iterrows():
            # Използваме info за по-добра видимост
            st.info(f"🕒 **{row['Период на доставка']}** — Цена: **{row['Цена (EUR/MWh)']} EUR**")

        # 3. Изчисляваме общата средна цена
        max_avg = top_12['Цена (EUR/MWh)'].mean()
        st.success(f"📈 СРЕДНА ЦЕНА (от избраните 12): **{max_avg:.2f} EUR/MWh**")
        
        # Графика за целия ден
        st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Грешка при четене: {e}")
        
