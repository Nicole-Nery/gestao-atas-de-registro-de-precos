import streamlit as st
from auth.funcoes_auth import *
from db import *
from home import show_home

def mostrar_tela_login_ou_cadastro_ou_home():
    
    modos_validos = ["login", "cadastro", "home"]

    if "modo" not in st.session_state or st.session_state["modo"] not in modos_validos:
        st.session_state["modo"] = "login"

    modo = st.session_state["modo"]
    
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

    if modo == "login":
        tela_login()
    elif modo == "cadastro":
        tela_cadastro()
    elif modo == "home":
        show_home()

def tela_login():
    st.markdown("""
        <style>
            .block-container {
                padding-top: 5vh;
                max-width: 500px;
                margin: auto;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="login-title">Login</h1>', unsafe_allow_html=True)

    with st.form("login_form", border=False):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            else:
                usuario_autenticado = autenticar_usuario(email, senha)
                if usuario_autenticado:
                    st.session_state.usuario = usuario_autenticado
                    st.session_state["modo"] = "home"
                    st.rerun()
                else:
                    st.error("E-mail ou senha inválidos.")

    if st.button("Não tem conta? Cadastre-se aqui."):
        st.session_state["modo"] = "cadastro"
        st.rerun()

def tela_cadastro():
    st.markdown("""
        <style>
            .block-container {
                padding-top: 5vh;
                max-width: 900px;
                margin: auto;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="login-title">Cadastro de usuário</h1>', unsafe_allow_html=True)

    with st.form("cadastro_form", border=False):
        nome = st.text_input("Nome Completo")
        cargo = st.selectbox("Cargo", ["Secretária", "Diretor financeiro", "Diretora Pedagógica", "Coordenadora", "Marketing"])
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Senha", type="password")

        cadastrar = st.form_submit_button("Cadastrar")

        if cadastrar:
            if not nome or not cargo or not email or not senha or not confirmar_senha:
                st.warning("Por favor, preencha todos os campos.")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            elif len(senha) < 6:
                st.error("A senha deve conter pelo menos 6 dígitos.")
            else:
                sucesso, mensagem = cadastrar_novo_usuario(supabase, nome, cargo, email, senha)
                if sucesso:
                    st.success(mensagem)
                else:
                    st.error(mensagem)

    if st.button("← Voltar para o login"):
        st.session_state["modo"] = "login"
        st.rerun()
