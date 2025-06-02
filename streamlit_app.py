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

# Modo
modos_validos = ["login", "cadastro", "home"]

placeholder = st.empty()
if "modo" not in st.session_state or st.session_state["modo"] not in modos_validos:
    st.session_state["modo"] = "login"

# CSS dinâmico com base no modo
modo = st.session_state.get("modo", "login")

if modo in ["login", "cadastro"]:
    st.markdown("""
        <style>
            .block-container {
                padding-top: 5vh;
                max-width: 1000px;
                margin: auto;
            }
        </style>
    """, unsafe_allow_html=True)

# Fluxo principal -------
if "usuario" not in st.session_state:
    if st.session_state["modo"] == "login":
        tela_login()
    else:
        tela_cadastro()
    st.stop()

# Exibe a tela de acordo com o modo atual
if st.session_state["modo"] == "login":
    tela_login()
elif st.session_state["modo"] == "cadastro":
    tela_cadastro()
elif st.session_state["modo"] == "home":
    show_home()

usuario = st.session_state.usuario
