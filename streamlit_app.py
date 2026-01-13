import streamlit as st
import pandas as pd

st.set_page_config(page_title="Анализатор на Цени", layout="centered")

st.title("📊 Пълен Дневен Анализ")
st.write("Търсене на най-висока средна цена за **целия ден**.")

uploaded_file = st.file_uploader("Избери файл", type=None)

if uploaded_file is not None:
    try:
        # Четем файла, като автоматично намираме къде започват данните
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        df.columns = [c.strip() for c in df.columns]
        
        # Превръщаме цената в число
        if df['Цена (EUR/MWh)'].dtype == object:
            df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].str.replace(',', '.').astype(float)

        # ТУК Е ПРОМЯНАТА: Гледаме всички данни, без филтър за 10:30
        df_all = df.copy()

        # Намираме ТОП 3 най-високи цени за целия ден
        top_3 = df_all.sort_values(by='Цена (EUR/MWh)', ascending=False).head(3)

        st.subheader("🏆 ТОП 3 Най-скъпи моменти (Целият ден)")
        for index, row in top_3.iterrows():
            st.info(f"🕒 **{row['Период на доставка']}** | Цена: **{row['Цена (EUR/MWh)']} EUR**")

        avg_price = top_3['Цена (EUR/MWh)'].mean()
        st.success(f"📈 МАКСИМАЛНА СРЕДНА ЦЕНА: **{avg_price:.2f} EUR/MWh**")
        
        # Графика на цялото денонощие
        st.line_chart(df_all.set_index('Период на доставка')['Цена (EUR/MWh)'])
        
    except Exception as e:
        st.error(f"Грешка при четене на файла: {e}")
