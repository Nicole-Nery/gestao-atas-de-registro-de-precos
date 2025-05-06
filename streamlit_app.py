import streamlit as st
import bcrypt
from home import show_home
from db import supabase

caminho_css = "style/main.css"

with open(caminho_css) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def autenticar_usuario(email, senha_digitada):
    res = supabase.table("usuarios").select("*").eq("email", email).execute()

    if res.data:
        usuario = res.data[0]
        senha_hash = usuario["senha"].encode('utf-8')
        if bcrypt.checkpw(senha_digitada.encode('utf-8'), senha_hash):
            return usuario
    return None

def login():
    with st.form:
        st.title("Login")
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        entrar = st.form_submit_button("Entrar")

        if entrar:
            if not email or not senha:
                st.warning("Preencha todos os campos.")
            elif autenticar_usuario(email, senha):
                st.success("Login bem-sucedido! Redirecionando...")
                st.session_state.usuario = {"email": email}
                st.experimental_rerun()
            else:
                st.error("E-mail ou senha inválidos.")

def cadastrar_usuario(supabase, nome, email, senha):
    try:
        # 1. Cria o usuário com e-mail e senha
        response = supabase.auth.sign_up({
            "email": email,
            "password": senha
        })

        # Verifica se houve erro na criação do auth
        if response.get("error"):
            return False, f"Erro ao criar usuário: {response['error']['message']}"

        user_id = response['user']['id']

        # 2. Salva dados adicionais na tabela "usuarios"
        dados_usuario = {
            "id": user_id,     # usa o mesmo ID do auth
            "nome": nome,
            "email": email
        }

        insert_response = supabase.table("usuarios").insert(dados_usuario).execute()

        if insert_response.error:
            return False, f"Erro ao salvar dados do usuário: {insert_response.error.message}"

        return True, "Usuário cadastrado com sucesso!"

    except Exception as e:
        return False, f"Erro inesperado: {str(e)}"


def cadastro():
    st.title("Cadastro de Usuário")
    
    with st.form("cadastro_form"):
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
            else:
                # Cadastrar no banco de dados
                try:
                    res = cadastrar_usuario(nome, email, senha)
                    if res.status_code == 201:
                        st.success("Cadastro realizado com sucesso!")
                    else:
                        st.error("Ocorreu um erro ao tentar cadastrar o usuário.")
                except Exception as e:
                    st.error(f"Erro: {e}")

# Fluxo principal -------
if "usuario" not in st.session_state:
    login()
    st.stop()

usuario = st.session_state.usuario

# Sidebar
st.sidebar.success(f"Logado como: {usuario['nome']}")
if st.sidebar.button("Sair"):
    del st.session_state.usuario
    st.rerun()

show_home()
