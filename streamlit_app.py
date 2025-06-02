import streamlit as st
import bcrypt
from home import show_home
from login_page import *
from db import supabase

st.set_page_config(page_title= "SIGAH", 
                page_icon= ("assets/icon.svg"), 
                layout = "wide")

# Estilo CSS
caminho_css = "style/main.css"
with open(caminho_css) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)



# Fluxo - Login ou cadastro
if "usuario" not in st.session_state:
    mostrar_tela_login_ou_cadastro()
    st.stop()
