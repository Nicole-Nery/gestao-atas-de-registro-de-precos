import streamlit as st
import pandas as pd

# Título do app
st.title("Gestão de Atas de Registro de Preços")

# Criar um DataFrame para armazenar os dados (simulação)
if "atas" not in st.session_state:
    st.session_state.atas = pd.DataFrame(columns=["Nome", "Fornecedor", "Validade", "Saldo"])

# Formulário para adicionar uma nova ata
with st.form("nova_ata"):
    nome = st.text_input("Nome da Ata")
    fornecedor = st.text_input("Fornecedor")
    validade = st.date_input("Validade")
    saldo = st.number_input("Saldo Inicial", min_value=0)
    submit = st.form_submit_button("Adicionar Ata")

    if submit:
        nova_linha = pd.DataFrame([[nome, fornecedor, validade, saldo]], columns=st.session_state.atas.columns)
        st.session_state.atas = pd.concat([st.session_state.atas, nova_linha], ignore_index=True)

# Mostrar a tabela de atas cadastradas
st.dataframe(st.session_state.atas)
