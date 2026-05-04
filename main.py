import streamlit as st

st.set_page_config(page_title="Nettrace", layout="wide")

pages = [
    st.Page("pages/IP.py", title="IP"),
    st.Page("pages/MAC.py", title="MAC"),
]

navigation = st.navigation(pages)
navigation.run()
