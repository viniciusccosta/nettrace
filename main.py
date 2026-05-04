import streamlit as st

st.set_page_config(page_title="Nettrace", layout="wide")

pg = st.navigation([st.Page("pages/IP_MAC.py", title="IP/MAC")])
pg.run()
