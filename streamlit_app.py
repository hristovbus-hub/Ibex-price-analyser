import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Резултати по блокове")
st.write("Най-скъпите 2 часа и 45 минути, групирани по периоди.")

# 📁 File uploader – вече приема CSV, XLS, XLSX
uploaded_file = st.file_uploader(
    "Избери файл",
    type=['csv', 'txt', 'xls', 'xlsx'],
    accept_multiple_files=False
)

if uploaded_file is not None:
    try:
        # Определяме разширението
        ext = os.path.splitext(uploaded_file.name)[1].lower()

        # Четене според типа файл
        if ext in ['.csv', '.txt']:
            df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
        elif ext in ['.xls', '.xlsx']:
            df = pd.read_excel(uploaded_file, skiprows=9)
        else:
            st.error("Неподдържан файлов формат.")
            st.stop()

        df.columns = [c.strip() for c in df.columns]

        # Вземаме само редовете с QH продукти
        df = df[df['Продукт'].astype(str).str.startswith('QH')].copy()

        # Нормализация на цената
        if df['Цена (EUR/MWh)'].dtype == object:
            df['Цена (EUR/MWh)'] = (
                df['Цена (EUR/MWh)']
                .astype(str)
                .str.replace(',', '.')
                .astype(float)
            )

        # Подреждаме по QH
        df['QH'] = df['Продукт'].str.extract(r'QH\s*(\d+)').astype(int)
        df = df.sort_values('QH').reset_index(drop=True)

        prices = df['Цена (EUR/MWh)'].tolist()
        n = len(prices)

        # 2) Префиксни суми
        prefix = [0.0] * (n + 1)
        for i in range(n):
            prefix[i + 1] = prefix[i] + prices[i]

        def segment_sum(start_idx, length):
            return prefix[start_idx + length] - prefix[start_idx]

        best_total_sum = None
        best_choice = None

        # 🔥 11 QH = 2 часа и 45 минути
        TOTAL_QH = 11

        # 3) Обхождаме всички разпределения на 11 QH в 3 периода
        for L1 in range(1, TOTAL_QH):
            for L2 in range(1, TOTAL_QH):
                L3 = TOTAL_QH - L1 - L2
                if L3 < 1:
                    continue

                for i1 in range(0, n - L1 + 1):
                    for i2 in range(i1 + L1, n - L2 + 1):
                        for i3 in range(i2 + L2, n - L3 + 1):
                            s1 = segment_sum(i1, L1)
                            s2 = segment_sum(i2, L2)
                            s3 = segment_sum(i3, L3)
                            total_sum = s1 + s2 + s3

                            if best_total_sum is None or total_sum > best_total_sum:
                                best_total_sum = total_sum
                                best_choice = ((i1, L1), (i2, L2), (i3, L3))

        if best_choice is None:
            st.error("Не е намерена комбинация от 3 периода с общо 11 QH.")
        else:
            (i1, L1), (i2, L2), (i3, L3) = best_choice

            blocks = []
            for (start_idx, length) in [(i1, L1), (i2, L2), (i3, L3)]:
                end_idx = start_idx + length - 1

                start_time = df.loc[start_idx, 'Период на доставка'].split('-')[0].strip()
                end_time = df.loc[end_idx, 'Период на доставка'].split('-')[1].strip()

                avg_price = df.loc[start_idx:end_idx, 'Цена (EUR/MWh)'].mean()
                blocks.append((start_time, end_time, length, avg_price))

            total_avg = best_total_sum / TOTAL_QH

            st.subheader("⏳ Периоди за работа:")
            for idx, (b_start, b_end, qh_len, b_avg) in enumerate(blocks, start=1):
                st.warning(
                    f"Период {idx}: 🕒 **{b_start} - {b_end}** "
                    f"({qh_len} QH) | Средна цена: **{b_avg:.2f} EUR/MWh**"
                )

            st.success(f"📈 ОБЩА СРЕДНА ЦЕНА (2ч 45м, 11 QH): **{total_avg:.2f} EUR/MWh**")

            st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Грешка: {e}")
