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

        best_total = None
        best_combo = None

        for i in range(len(df)):
            for l1 in range(1, 12):
                if i + l1 > len(df):
                    continue
                for j in range(i + l1, len(df)):
                    for l2 in range(1, 12 - l1):
                        if j + l2 > len(df):
                            continue
                        for k in range(j + l2, len(df)):
                            l3 = 12 - l1 - l2
                            if k + l3 > len(df):
                                continue

                            s1 = df.loc[i:i+l1-1, 'Цена (EUR/MWh)'].sum()
                            s2 = df.loc[j:j+l2-1, 'Цена (EUR/MWh)'].sum()
                            s3 = df.loc[k:k+l3-1, 'Цена (EUR/MWh)'].sum()
                            total = s1 + s2 + s3

                            if best_total is None or total > best_total:
                                best_total = total
                                best_combo = [(i, l1), (j, l2), (k, l3)]

        if best_combo is None:
            st.error("Не е намерена комбинация от 3 периода с общо 12 QH.")
        else:
            blocks = []
            for start, length in best_combo:
                end = start + length - 1
                start_time = df.loc[start, 'Период на доставка'].split('-')[0].strip()
                end_time = df.loc[end, 'Период на доставка'].split('-')[1].strip()
                avg = df.loc[start:end, 'Цена (EUR/MWh)'].mean()
                blocks.append((start_time, end_time, length, avg))

            total_avg = best_total / 12.0
            st.subheader(f"📈 ОБЩА СРЕДНА ЦЕНА (3ч): **{total_avg:.2f} EUR/MWh**")

            for idx, (start, end, qh, avg) in enumerate(blocks, start=1):
                st.warning(
                    f"Период {idx}: 🕒 **{start} – {end}** "
                    f"({qh} QH) | Средна: **{avg:.2f} EUR/MWh**"
                )

            st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"⚠️ Грешка: {e}")
