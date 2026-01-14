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
        df = df[df['Продукт'].astype(str).str.startswith('QH')].copy()

        df['Цена (EUR/MWh)'] = (
            df['Цена (EUR/MWh)']
            .astype(str)
            .str.replace(',', '.')
            .astype(float)
        )

        df['QH'] = df['Продукт'].str.extract(r'QH\s*(\d+)').astype(int)
        df = df.sort_values('QH').reset_index(drop=True)

        # Генерираме всички възможни интервали
        intervals = []
        for start in range(len(df)):
            for end in range(start, len(df)):
                length = end - start + 1
                avg = df.loc[start:end, 'Цена (EUR/MWh)'].mean()
                intervals.append((start, end, length, avg))

        # Търсим най-добрата комбинация от 3 интервала с общо 12 QH и без застъпване
        best = None
        for a in intervals:
            for b in intervals:
                for c in intervals:
                    total_len = a[2] + b[2] + c[2]
                    if total_len != 12:
                        continue
                    # Проверка за застъпване
                    if a[1] < b[0] or b[1] < c[0] or a[1] < c[0]:
                        total_avg = (
                            a[3]*a[2] + b[3]*b[2] + c[3]*c[2]
                        ) / 12
                        if best is None or total_avg > best[0]:
                            best = (total_avg, a, b, c)

        if best is None:
            st.error("Не е намерена комбинация от 3 периода с общо 12 QH.")
        else:
            total_avg, a, b, c = best
            st.subheader(f"📈 ОБЩА СРЕДНА ЦЕНА (3ч): **{total_avg:.2f} EUR/MWh**")

            for idx, (start, end, length, avg) in enumerate([a, b, c], start=1):
                start_time = df.loc[start, 'Период на доставка'].split('-')[0].strip()
                end_time = df.loc[end, 'Период на доставка'].split('-')[1].strip()
                st.warning(
                    f"Период {idx}: 🕒 **{start_time} – {end_time}** "
                    f"({length} QH) | Средна: **{avg:.2f} EUR/MWh**"
                )

            st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"⚠️ Грешка: {e}")
