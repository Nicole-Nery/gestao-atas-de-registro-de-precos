import streamlit as st
from login_page import *

st.set_page_config(page_title= "SIGAH", 
                page_icon= ("assets/icon.svg"), 
                layout = "wide")

# Estilo CSS
caminho_css = "style/main.css"
with open(caminho_css) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


mostrar_tela_login_ou_cadastro_ou_home()
