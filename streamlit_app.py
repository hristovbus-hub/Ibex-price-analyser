import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="IBEX Оптимизатор", layout="centered")

st.title("📊 Резултати по блокове")
st.write("Най-скъпите 2 часа и 45 минути, групирани по периоди.")

# 📁 File uploader – приема CSV, TXT, XLS, XLSX
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
        elif ext == '.xls':
            df = pd.read_excel(uploaded_file, skiprows=9, engine='xlrd')
        elif ext == '.xlsx':
            df = pd.read_excel(uploaded_file, skiprows=9, engine='openpyxl')
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

        # Подреждаме по
