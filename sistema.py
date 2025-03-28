import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Inicializa session state para armazenar dados temporários
if "atas" not in st.session_state:
    st.session_state.atas = []
if "fornecedores" not in st.session_state:
    st.session_state.fornecedores = []
if "empenhos" not in st.session_state:
    st.session_state.empenhos = []

# Layout com abas
tabs = st.tabs(["Registro de Atas", "Cadastro de Fornecedores", "Registro de Empenhos", "Histórico de Empenhos", "Relatórios"])

# Registro de Atas
with tabs[0]:
    st.header("Registro de Atas")

    # Atualizar lista de fornecedores (sempre pegar os fornecedores cadastrados)
    fornecedores_cadastrados = ["Selecione"] + [f["nome"] for f in st.session_state.fornecedores]

    # Formulário para cadastrar nova ATA
    with st.form("nova_ata"):
        nome_ata = st.text_input("Nome da ATA")
        data_ata = st.date_input("Data da ATA")
        validade_ata = st.date_input("Validade da ATA", min_value=data_ata)
        fornecedor = st.selectbox("Fornecedor", fornecedores_cadastrados, key="select_fornecedor")
        link_ata = st.text_input("Link para o PDF da ATA")
        submit_ata = st.form_submit_button("Cadastrar ATA")

        if submit_ata and nome_ata and data_ata and fornecedor != "Selecione":
            st.session_state.atas.append({
                "nome": nome_ata,
                "data": data_ata,
                "validade": validade_ata,
                "fornecedor": fornecedor,
                "equipamentos": [],
                "link": link_ata
            })
            st.success(f"ATA '{nome_ata}' cadastrada com sucesso!")

    # Adicionando Equipamentos à ATA
    st.subheader("Cadastrar Equipamentos para a ATA")
    if len(st.session_state.atas) > 0:
        ata_selecionada = st.selectbox("Selecione a ATA", ["Selecione"] + [a["nome"] for a in st.session_state.atas], key="select_ata")
        
        if ata_selecionada != "Selecione":
            ata = next(a for a in st.session_state.atas if a["nome"] == ata_selecionada)
            with st.form("equipamento_ata"):
                st.subheader("Adicione os Equipamentos")

                # Formulário para adicionar equipamento
                especificacao = st.text_input("Especificação")
                marca_modelo = st.text_input("Marca/Modelo")
                codigo = st.text_input("Código")
                unidade = st.text_input("Unidade")
                quantidade = st.number_input("Quantidade", min_value=1, step=1)
                saldo_disponivel = st.number_input("Saldo Disponível", min_value=0, step=1)
                valor_unitario = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
                valor_total = valor_unitario * quantidade
                submit_equipamento = st.form_submit_button("Adicionar Equipamento")

                if submit_equipamento and especificacao and marca_modelo:
                    # Adicionando o equipamento à ata
                    ata["equipamentos"].append({
                        "especificacao": especificacao,
                        "marca_modelo": marca_modelo,
                        "codigo": codigo,
                        "unidade": unidade,
                        "quantidade": quantidade,
                        "saldo_disponivel": saldo_disponivel,
                        "valor_unitario": valor_unitario,
                        "valor_total": valor_total
                    })
                    st.success(f"Equipamento '{especificacao}' adicionado com sucesso!")

            # Exibir equipamentos cadastrados para a ATA selecionada
            if ata["equipamentos"]:
                equipamentos_df = pd.DataFrame(ata["equipamentos"])
                st.subheader("Equipamentos Cadastrados")
                st.dataframe(equipamentos_df)
            else:
                st.info("Nenhum equipamento cadastrado ainda.")
    else:
        st.info("Nenhuma ATA cadastrada para adicionar equipamentos.")
        
# Registro de Fornecedores
with tabs[1]:
    st.header("Cadastro de Fornecedor")

    # Formulário para cadastrar fornecedor
    with st.form("novo_fornecedor"):
        nome_fornecedor = st.text_input("Nome do Fornecedor")
        cnpj = st.text_input("CNPJ")
        info1 = st.text_input("Informação 1")
        info2 = st.text_input("Informação 2")
        observacao = st.text_area("Observação")
        submit_fornecedor = st.form_submit_button("Cadastrar Fornecedor")

        if submit_fornecedor and nome_fornecedor and cnpj:
            st.session_state.fornecedores.append({
                "nome": nome_fornecedor,
                "cnpj": cnpj,
                "info1": info1,
                "info2": info2,
                "observacao": observacao
            })
            st.success(f"Fornecedor '{nome_fornecedor}' cadastrado!")

    # Listagem de fornecedores
    st.subheader("Fornecedores cadastrados")
    if st.session_state.fornecedores:
        fornecedores_df = pd.DataFrame(st.session_state.fornecedores)
        st.dataframe(fornecedores_df)
    else:
        st.info("Nenhum fornecedor cadastrado ainda.")

# Registro de Empenhos
with tabs[2]:
    st.header("Registro de Empenhos")

    # Seleção da ATA e equipamento
    ata_selecionada = st.selectbox("Selecione a ATA", ["Selecione"] + [a["nome"] for a in st.session_state.atas], key="select_empenho_ata")
    equipamento = st.text_input("Nome do Equipamento")
    quantidade = st.number_input("Quantidade", min_value=1, step=1)
    registrar_empenho = st.button("Registrar Empenho")

    if registrar_empenho and ata_selecionada != "Selecione" and equipamento:
        # Atualizando o saldo de equipamentos ao registrar empenho
        ata = next(a for a in st.session_state.atas if a["nome"] == ata_selecionada)
        for equip in ata["equipamentos"]:
            if equip["especificacao"] == equipamento:
                if equip["saldo_disponivel"] >= quantidade:
                    equip["saldo_disponivel"] -= quantidade
                    st.session_state.empenhos.append({"ata": ata_selecionada, "equipamento": equipamento, "quantidade": quantidade})
                    st.success("Empenho registrado!")
                    break
                else:
                    st.warning("Quantidade insuficiente disponível.")
                    break

# Histórico de Empenhos
with tabs[3]:
    st.header("Histórico de Empenhos")

    # Seleção de ATA para filtrar empenhos
    ata_filtro = st.selectbox("Filtrar por ATA", ["Todas"] + [a["nome"] for a in st.session_state.atas], key="select_filtro_ata")
    
    if st.session_state.empenhos:
        df_empenhos = pd.DataFrame(st.session_state.empenhos)
        
        if ata_filtro != "Todas":
            df_empenhos = df_empenhos[df_empenhos["ata"] == ata_filtro]
        
        st.dataframe(df_empenhos)
    else:
        st.info("Nenhum empenho registrado ainda.")

# Relatórios de Consumo e Status
with tabs[4]:
    st.header("Relatórios de Consumo e Status")

    # Relatório de consumo por ata e equipamento
    relatorio_consumo = []
    for ata in st.session_state.atas:
        for equip in ata["equipamentos"]:
            saldo_utilizado = equip["quantidade"] - equip["saldo_disponivel"]
            relatorio_consumo.append({
                "ATA": ata["nome"],
                "Equipamento": equip["especificacao"],
                "Saldo Utilizado": saldo_utilizado,
                "Saldo Disponível": equip["saldo_disponivel"],
                "Data de Validade": ata["validade"]
            })

    if relatorio_consumo:
        relatorio_df = pd.DataFrame(relatorio_consumo)
        st.dataframe(relatorio_df)
    else:
        st.info("Nenhum consumo registrado ainda.")
    
    # Alerta para atas vencendo em 7 dias
    hoje = datetime.today().date()
    alertas_vencimento = [ata for ata in st.session_state.atas if ata["validade"] <= hoje + timedelta(days=7)]
    
    if alertas_vencimento:
        st.warning("Alertas de vencimento de atas em 7 dias:")
        for alerta in alertas_vencimento:
            st.write(f"ATA: {alerta['nome']} - Validade: {alerta['validade']}")
    else:
        st.info("Nenhuma ATA vencendo em 7 dias.")
