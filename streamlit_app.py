import streamlit as st
import pandas as pd

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Резултати по блокове")
st.write("Най-скъпите 3 часа, групирани по периоди.")

uploaded_files = st.file_uploader("Избери един или повече файлове", type=['csv', 'txt'], accept_multiple_files=True)

if uploaded_file is not None:
    try:
        # 1) Четене на файла – почти като при теб
        df = pd.read_csv(uploaded_file, sep=';', skiprows=9)
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

        # Уверяваме се, че редовете са подредени по QH
        df['QH'] = df['Продукт'].str.extract(r'QH\s*(\d+)').astype(int)
        df = df.sort_values('QH').reset_index(drop=True)

        prices = df['Цена (EUR/MWh)'].tolist()
        n = len(prices)

        # 2) Префиксни суми за бързо смятане на суми по интервали
        prefix = [0.0] * (n + 1)
        for i in range(n):
            prefix[i + 1] = prefix[i] + prices[i]

        def segment_sum(start_idx, length):
            """Сума на цените от start_idx (вкл.) за 'length' QH."""
            return prefix[start_idx + length] - prefix[start_idx]

        best_total_sum = None
        best_choice = None  # ( (i1, L1), (i2, L2), (i3, L3) )

        # 3) Обхождаме всички разпределения на 12 QH в 3 периода
        for L1 in range(1, 12):          # поне 1 QH
            for L2 in range(1, 12):
                L3 = 12 - L1 - L2
                if L3 < 1:
                    continue

                # 4) За дадени L1, L2, L3 търсим всички възможни позиции без застъпване
                for i1 in range(0, n - L1 + 1):
                    for i2 in range(i1 + L1, n - L2 + 1):
                        for i3 in range(i2 + L2, n - L3 + 1):
                            s1 = segment_sum(i1, L1)
                            s2 = segment_sum(i2, L2)
                            s3 = segment_sum(i3, L3)
                            total_sum = s1 + s2 + s3  # максимизираме сумата → и средната ще е макс

                            if best_total_sum is None or total_sum > best_total_sum:
                                best_total_sum = total_sum
                                best_choice = ((i1, L1), (i2, L2), (i3, L3))

        if best_choice is None:
            st.error("Не е намерена комбинация от 3 периода с общо 12 QH.")
        else:
            # 5) Изчисляваме и показваме резултатите
            (i1, L1), (i2, L2), (i3, L3) = best_choice

            blocks = []
            for (start_idx, length) in [(i1, L1), (i2, L2), (i3, L3)]:
                end_idx = start_idx + length - 1

                # 'Период на доставка' е от вида 'HH:MM - HH:MM'
                start_time = df.loc[start_idx, 'Период на доставка'].split('-')[0].strip()
                end_time = df.loc[end_idx, 'Период на доставка'].split('-')[1].strip()

                avg_price = df.loc[start_idx:end_idx, 'Цена (EUR/MWh)'].mean()
                blocks.append((start_time, end_time, length, avg_price))

            total_avg = best_total_sum / 12.0

            st.subheader("⏳ Периоди за работа:")
            for idx, (b_start, b_end, qh_len, b_avg) in enumerate(blocks, start=1):
                st.warning(
                    f"Период {idx}: 🕒 **{b_start} - {b_end}** "
                    f"({qh_len} QH) | Средна цена: **{b_avg:.2f} EUR/MWh**"
                )

            st.success(f"📈 ОБЩА СРЕДНА ЦЕНА (3ч, 12 QH): **{total_avg:.2f} EUR/MWh**")

            # Графика (както при теб)
            st.line_chart(df.set_index('Период на доставка')['Цена (EUR/MWh)'])

    except Exception as e:
        st.error(f"Грешка: {e}")
