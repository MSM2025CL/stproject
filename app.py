import streamlit as st


pages = {"Buscador": [st.Page("main.py")], "Reporte": [st.Page("report.py")]}

pg = st.navigation(pages, position="hidden")
pg.run()
