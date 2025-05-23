import streamlit as st
import bcrypt
from home import show_home
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

def autenticar_usuario(email, senha_digitada):
    res = supabase.table("usuarios").select("*").eq("email", email).execute()

    if res.data:
        usuario = res.data[0]
        senha_hash = usuario["senha"].encode('utf-8')
        if bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash):
            return usuario
    return None

# Tela de login
def login():
    st.title("Login")

    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            elif autenticar_usuario(email, senha):
                usuario_autenticado = autenticar_usuario(email, senha)
                st.session_state.usuario = usuario_autenticado
                st.session_state["modo"] = "home"
                st.rerun()
                usuario = st.session_state.get("usuario", {})
                
            else:
                st.error("E-mail ou senha inválidos.")

    st.markdown("---")
    if st.button("Não tem conta? Cadastre-se aqui."):
        st.session_state["modo"] = "cadastro"
        st.rerun()


def cadastrar_novo_usuario(supabase, nome, email, senha):
    try:
        # Criptografa a senha
        hashed_password = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 1. Cria o usuário com e-mail e senha
        response = supabase.auth.sign_up({
            "email": email,
            "password": senha
        })

        # Verifica se houve erro na criação do auth
        if response.user is None:  # Verifica se o usuário não foi criado
            return False, f"Erro ao criar usuário: {response.message}"

        user_id = response.user.id  # Acessando o ID do usuário

        # 2. Salva dados adicionais na tabela "usuarios"
        dados_usuario = {
            "id": user_id,     # usa o mesmo ID do auth
            "nome": nome,
            "email": email,
            "senha": hashed_password
        }
        try:
            supabase.table("usuarios").insert(dados_usuario).execute()
            return True, "Usuário cadastrado com sucesso!"
        except Exception as e: 
            return False, f"Erro ao salvar dados do usuário: {e}"

    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"


def cadastro():    
    with st.form("cadastro_form"):
        st.header("Cadastro de usuário")

        nome = st.text_input("Nome Completo")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Senha", type="password")
        
        cadastrar = st.form_submit_button("Cadastrar")

        if cadastrar:
            if not nome or not email or not senha or not confirmar_senha:
                st.warning("Por favor, preencha todos os campos.")
            elif senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            elif len(senha) < 6:
                st.error("A senha deve conter pelo menos 6 dígitos.")
            else:
                # Cadastrar no banco de dados
                try:
                    sucesso, mensagem = cadastrar_novo_usuario(supabase, nome, email, senha)
                    if sucesso:
                        st.success(mensagem)
                    else:
                        st.error(mensagem)
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.markdown("---")
    voltar_login = st.button("← Voltar para o login")
    if voltar_login:
        st.session_state["modo"] = "login"
        st.rerun()

# Fluxo principal -------
if "usuario" not in st.session_state:
    if st.session_state["modo"] == "login":
        login()
    else:
        cadastro()
    st.stop()

# Exibe a tela de acordo com o modo atual
if st.session_state["modo"] == "login":
    login()
elif st.session_state["modo"] == "cadastro":
    cadastro()
elif st.session_state["modo"] == "home":
    show_home()

usuario = st.session_state.usuario
