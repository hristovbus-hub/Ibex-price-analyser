import streamlit as st
import pandas as pd

st.set_page_config(page_title="Price Analyzer", layout="centered")

st.title("📊 Анализ на цени за деня")
st.write("Качи CSV файла, за да намериш най-скъпите периоди.")

uploaded_file = st.file_uploader("Избери файл", type=['csv'])

if uploaded_file is not None:
    # Зареждане на данните
    df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
    df.columns = [c.strip() for c in df.columns]
    
    # Превръщане на цената в число
    if df['Цена (EUR/MWh)'].dtype == object:
        df['Цена (EUR/MWh)'] = df['Цена (EUR/MWh)'].str.replace(',', '.').astype(float)

    # Филтър след 10:30 (QH 43+)
    df['QH_num'] = df['Продукт'].str.extract('(\d+)').astype(int)
    df_after = df[df['QH_num'] >= 43].copy()

    # Намиране на ТОП 3 периода
    top_3 = df_after.sort_values(by='Цена (EUR/MWh)', ascending=False).head(3)

    st.subheader("🏆 Най-скъпи периоди (след 10:30)")
    for index, row in top_3.iterrows():
        st.info(f"🕒 **{row['Период на доставка']}** | Цена: **{row['Цена (EUR/MWh)']} EUR**")

    avg_price = top_3['Цена (EUR/MWh)'].mean()
    st.success(f"📈 Средна цена на ТОП 3: **{avg_price:.2f} EUR/MWh**")
    
    # Графика за визуализация
    st.line_chart(df_after.set_index('Период на доставка')['Цена (EUR/MWh)'])

