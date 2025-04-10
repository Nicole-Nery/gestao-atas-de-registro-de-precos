import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from supabase import create_client, Client

# Conectar ao Supabase
SUPABASE_URL = "https://btstungeitzcizcysupd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0c3R1bmdlaXR6Y2l6Y3lzdXBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQwNjAxNTUsImV4cCI6MjA1OTYzNjE1NX0.L1KZfGO_9Cq7iOGtdDVD4bGp02955s65fjcK2I1jntc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Alterando o nome da página e o ícone
st.set_page_config(page_title= "Gestão de ARP", 
                   page_icon= "📄")
st.title("Sistema de Gestão de Atas de Registro de Preços")
st.write("Bem-vindo ao sistema de controle de atas, onde você pode gerenciar saldos, acompanhar validade e gerar relatórios.")

# Estabelecendo o layout com abas
tabs = st.tabs(["Fornecedores", "Atas", "Empenhos", "Histórico de Empenhos", "Relatórios"])

# Registro de Fornecedores
with tabs[0]:
    st.header("Cadastro de Fornecedores")

    # Formulário para cadastrar fornecedor
    with st.form("novo_fornecedor", clear_on_submit=True):
        nome_fornecedor = st.text_input("Nome do Fornecedor")
        cnpj = st.text_input("CNPJ")
        email = st.text_input("E-mail")
        endereco = st.text_input("Endereço")
        telefone = st.text_input("Telefone")
        submit_fornecedor = st.form_submit_button("Cadastrar Fornecedor")

    if submit_fornecedor and nome_fornecedor and cnpj:
        try:
            response = supabase.table("fornecedores").insert({
                "nome": nome_fornecedor,
                "cnpj": cnpj,
                "email": email,
                "endereco": endereco,
                "telefone": telefone
            }).execute()
            st.success(f"Fornecedor '{nome_fornecedor}' cadastrado com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao cadastrar fornecedor: {e}.")

    else:
        st.warning("Preencha todos os campos obrigatórios.")

    # Listagem de fornecedores
    st.subheader("Fornecedores cadastrados")
    try:
        response = supabase.table("fornecedores").select("nome, cnpj, email, endereco, telefone").order("nome").execute()
        fornecedores_result = response.data # Devolve um dicionário
        
        df_fornecedores = pd.DataFrame(fornecedores_result)
        df_fornecedores = df_fornecedores.rename(columns={
            "nome": "Nome",
            "cnpj": "CNPJ",
            "email": "E-mail",
            "endereco": "Endereço",
            "telefone": "Telefone"
        })
        st.dataframe(df_fornecedores)

    except Exception as e:
        st.error(f"Erro ao buscar fornecedor: {e}.")

# Registro de Atas
with tabs[1]:
    st.header("Registro de Atas")

    try:
        response = supabase.table("fornecedores").select("id, nome").order("nome").execute()
        fornecedores_result = response.data
        fornecedores_dict = {f["nome"]: f["id"] for f in fornecedores_result}
        fornecedores_cadastrados = ["Selecione"] + list(fornecedores_dict.keys())

    except Exception as e:
        st.error(f"Erro ao buscar fornecedores: {e}")
        fornecedores_cadastrados = ["Selecione"]
        fornecedores_dict = {}

    # Formulário para cadastrar nova Ata
    with st.form("nova_ata", clear_on_submit=True):
        nome_ata = st.text_input("Nome da Ata")
        data_ata = st.date_input("Data da Ata", format="DD/MM/YYYY")
        validade_ata = st.date_input("Validade da Ata", min_value=data_ata, format="DD/MM/YYYY")
        fornecedor_nome = st.selectbox("Fornecedor", fornecedores_cadastrados,key="selecione_fornecedor_nome")
        link_ata = st.text_input("Link para o PDF da Ata")

        submit_ata = st.form_submit_button("Cadastrar Ata")

        if submit_ata:
            if nome_ata and data_ata and validade_ata and (fornecedor_nome != "Selecione"):
                try:
                    fornecedor_id = fornecedores_dict[fornecedor_nome]
                    
                    supabase.table("atas").insert({
                        "nome": nome_ata,
                        "data_inicio": data_ata.isoformat(),
                        "data_validade": validade_ata.isoformat(),
                        "fornecedor_id": fornecedor_id,
                        "link_ata": link_ata
                    }).execute()
                    st.success(f"Ata '{nome_ata}' cadastrada com sucesso!")

                except Exception as e:
                    st.error(f"Erro ao cadastrar a Ata: {e}")
            else:
                st.warning("Preencha todos os campos obrigatórios.")
            

    # Adicionando Equipamentos à Ata

    st.subheader("Cadastro de Equipamentos para Ata")

    try:
        response = supabase.table("atas").select("id, nome").order("nome").execute()
        atas_result = response.data
        atas_dict = {a["nome"]: a["id"] for a in atas_result}
        atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

    except Exception as e:
        st.error(f"Erro ao buscar atas: {e}")
        atas_cadastradas = ["Selecione"]
        atas_dict = {}

    ata_nome = st.selectbox("Selecione a Ata", atas_cadastradas, key="selecione_ata_nome")

    if ata_nome != "Selecione":
        ata_id = atas_dict[ata_nome]

        with st.form("novo_equipamento", clear_on_submit=True):
            st.subheader("Adicionar Equipamento")

            especificacao = st.text_input("Especificação")
            marca_modelo = st.text_input("Marca/Modelo")
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            saldo_disponivel = st.number_input("Saldo disponível", min_value=0, step=1)
            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f")
            valor_total = valor_unitario * quantidade

            submit_equipamento = st.form_submit_button("Adicionar Equipamento")

            if submit_equipamento and especificacao and marca_modelo and quantidade and saldo_disponivel and valor_unitario:
                try:
                    response = supabase.table("equipamentos").insert({
                        "ata_id": ata_id,
                        "especificacao": especificacao,
                        "marca_modelo": marca_modelo,
                        "quantidade": quantidade,
                        "saldo_disponivel": saldo_disponivel,
                        "valor_unitario": valor_unitario,
                        "valor_total": valor_total
                    }).execute()
                    st.success(f"Equipamento '{especificacao}' cadastrado com sucesso na ata '{ata_nome}'!")
                except Exception as e:
                    st.error(f"Erro ao cadastrar equipamento: {e}")
            else:
                st.warning("Preencha todos os campos obrigatórios.")

    # Visualização dos dados cadastrados na Ata selecionada
    st.subheader("Visualizar Atas Cadastradas")

    try:
        # Buscar todas as atas com nome do fornecedor
        response = supabase.table("atas").select("id, nome, data_inicio, data_validade, link_ata, fornecedores(nome)").order("data_inicio", desc=True).execute()
        atas_result = response.data
        atas_dict = {a["nome"]: a["id"] for a in atas_result}
        atas_opcoes = ["Selecione"] + list(atas_dict.keys())

    except Exception as e:
        st.error(f"Erro ao buscar atas: {e}")
        atas_opcoes = ["Selecione"]
        atas_dict = {}

    ata_visualizar = st.selectbox("Selecione uma Ata para visualizar", atas_opcoes, key="selecione_ata_visualizar")

    if ata_visualizar != "Selecione":
        ata_id = atas_dict[ata_visualizar]

        # Buscar os dados da Ata selecionada
        ata_info = next((a for a in atas_result if a["id"] == ata_id), None)

        if ata_info:
            nome = ata_info["nome"]
            data_ata = ata_info["data_inicio"]
            validade_ata = ata_info["data_validade"]
            link_pdf = ata_info.get("link_ata", "")
            fornecedor_nome = ata_info["fornecedores"]["nome"]

            st.markdown(f"**Nome:** {nome}")
            st.markdown(f"**Data da Ata:** {pd.to_datetime(data_ata).strftime('%d/%m/%Y')}")
            st.markdown(f"**Validade:** {pd.to_datetime(validade_ata).strftime('%d/%m/%Y')}")
            st.markdown(f"**Fornecedor:** {fornecedor_nome}")
            if link_pdf:
                st.markdown(f"[Abrir PDF da Ata]({link_pdf})", unsafe_allow_html=True)

            # Buscar os equipamentos dessa ata
            try:
                response = supabase.table("equipamentos").select(
                    "especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario, valor_total"
                ).eq("ata_id", ata_id).execute()
                equipamentos = response.data

                st.subheader("Equipamentos Cadastrados")

                if equipamentos:
                    df_equip = pd.DataFrame(equipamentos)
                    df_equip = df_equip.rename(columns={
                        "especificacao": "Especificação",
                        "marca_modelo": "Marca/Modelo",
                        "quantidade": "Quantidade",
                        "saldo_disponivel": "Saldo Disponível",
                        "valor_unitario": "Valor Unitário",
                        "valor_total": "Valor Total"
                    })
                    st.dataframe(df_equip)
                else:
                    st.info("Nenhum equipamento cadastrado para esta Ata.")
            except Exception as e:
                st.error(f"Erro ao buscar equipamentos: {e}")

                
with tabs[2]:
    st.header("Registro de Empenhos")

    try:
        # Buscar atas cadastradas
        response = supabase.table("atas").select("id, nome").order("nome", desc=False).execute()
        atas_result = response.data
        atas_dict = {a["nome"]: a["id"] for a in atas_result}
        atas_cadastradas = ["Selecione"] + list(atas_dict.keys())
    except Exception as e:
        st.error(f"Erro ao buscar atas: {e}")
        atas_cadastradas = ["Selecione"]
        atas_dict = {}

    ata_nome = st.selectbox("Selecione a Ata", atas_cadastradas, key="selecione_ata_nome_empenho")

    if ata_nome != "Selecione":
        ata_id = atas_dict[ata_nome]

        try:
            # Buscar equipamentos com saldo > 0
            response = supabase.table("equipamentos").select("id, especificacao, saldo_disponivel").eq("ata_id", ata_id).gt("saldo_disponivel", 0).execute()
            equipamentos_result = response.data

            if equipamentos_result:
                equipamentos_dict = {e["especificacao"]: (e["id"], e["saldo_disponivel"]) for e in equipamentos_result}
                equip_opcoes = ["Selecione"] + list(equipamentos_dict.keys())

                equipamento_nome = st.selectbox("Selecione o Equipamento", equip_opcoes, key="selecione_equipamento_nome")

                if equipamento_nome != "Selecione":
                    equipamento_id, saldo_disp = equipamentos_dict[equipamento_nome]
                    quantidade = st.number_input("Quantidade empenhada", min_value=1, max_value=saldo_disp, step=1)
                    data_empenho = st.date_input("Data do Empenho", format="DD/MM/YYYY")
                    observacao = st.text_input("Observação (opcional)")

                    if st.button("Registrar Empenho"):
                        try:
                            # Inserir empenho
                            supabase.table("empenhos").insert({
                                "equipamento_id": equipamento_id,
                                "quantidade_empenhada": quantidade,
                                "data_empenho": data_empenho.isoformat(),
                                "observacao": observacao
                            }).execute()

                            # Atualizar saldo do equipamento
                            supabase.table("equipamentos").update({
                                "saldo_disponivel": saldo_disp - quantidade
                            }).eq("id", equipamento_id).execute()

                            st.success("Empenho registrado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao registrar empenho: {e}")
            else:
                st.warning("Nenhum equipamento com saldo disponível para esta Ata.")
        except Exception as e:
            st.error(f"Erro ao buscar equipamentos: {e}")

        # Exibir empenhos registrados
        st.subheader("Empenhos Registrados para esta Ata")
        try:
            response = supabase.rpc("empenhos_por_ata", {"ata_id_param": ata_id}).execute()
            empenhos = response.data

            if empenhos:
                df_empenhos = pd.DataFrame(empenhos)
                df_empenhos = df_empenhos.rename(columns={
                    "especificacao": "Equipamento",
                    "quantidade_empenhada": "Quantidade",
                    "data_empenho": "Data",
                    "observacao": "Observação"
                })
                df_empenhos["Data"] = pd.to_datetime(df_empenhos["Data"]).dt.strftime('%d/%m/%Y')
                st.dataframe(df_empenhos)
            else:
                st.info("Nenhum empenho registrado para esta Ata.")
        except Exception as e:
            st.error(f"Erro ao buscar empenhos: {e}")

# Histórico de Empenhos
with tabs[3]:
    st.header("Histórico de Empenhos")

    try:
        # Buscar atas
        atas_response = supabase.table("atas").select("id, nome").order("nome").execute()
        atas_data = atas_response.data
        atas_dict = {ata["nome"]: ata["id"] for ata in atas_data}
        atas_opcoes = ["Todas"] + list(atas_dict.keys())

        ata_filtro = st.selectbox("Filtrar por Ata", atas_opcoes, key="selecione_ata_filtro")

        # Buscar todos os equipamentos (para cruzar depois com atas e empenhos)
        equipamentos_response = supabase.table("equipamentos").select("id, especificacao, ata_id").execute()
        equipamentos_data = equipamentos_response.data
        equipamentos_dict = {eq["id"]: eq for eq in equipamentos_data}

        # Buscar todos os empenhos
        empenhos_response = supabase.table("empenhos").select("*").order("data_empenho", desc=True).execute()
        empenhos_data = empenhos_response.data

        empenhos_filtrados = []
        for emp in empenhos_data:
            equipamento = equipamentos_dict.get(emp["equipamento_id"])
            if not equipamento:
                continue
            ata_id = equipamento["ata_id"]
            ata_nome = next((nome for nome, id_ in atas_dict.items() if id_ == ata_id), "Desconhecida")

            if ata_filtro == "Todas" or atas_dict[ata_filtro] == ata_id:
                empenhos_filtrados.append({
                    "Ata": ata_nome,
                    "Equipamento": equipamento["especificacao"],
                    "Quantidade": emp["quantidade_empenhada"],
                    "Data do Empenho": emp["data_empenho"],
                    "Observação": emp["observacao"]
                })

        if empenhos_filtrados:
            df_empenhos = pd.DataFrame(empenhos_filtrados)
            df_empenhos["Data do Empenho"] = pd.to_datetime(df_empenhos["Data do Empenho"]).dt.strftime('%d/%m/%Y')
            st.dataframe(df_empenhos)
        else:
            st.info("Nenhum empenho registrado ainda.")
    except Exception as e:
        st.error(f"Erro ao buscar empenhos: {e}")


# Aba 4: Relatórios de Consumo e Status
with tabs[4]:
    st.header("Relatórios de Consumo e Status")

    try:
        # Buscar atas
        atas_response = supabase.table("atas").select("id, nome, data_validade").execute()
        atas_data = {ata["id"]: ata for ata in atas_response.data}

        # Buscar equipamentos
        equipamentos_response = supabase.table("equipamentos").select("especificacao, quantidade, saldo_disponivel, ata_id").order("ata_id").execute()
        equipamentos_data = equipamentos_response.data

        if equipamentos_data:
            relatorio_consumo = []
            for eq in equipamentos_data:
                ata = atas_data.get(eq["ata_id"])
                if not ata:
                    continue
                saldo_utilizado = eq["quantidade"] - eq["saldo_disponivel"]
                relatorio_consumo.append({
                    "Ata": ata["nome"],
                    "Equipamento": eq["especificacao"],
                    "Saldo Utilizado": saldo_utilizado,
                    "Saldo Disponível": eq["saldo_disponivel"],
                    "Data de Validade": ata["data_validade"]
                })

            relatorio_df = pd.DataFrame(relatorio_consumo)
            relatorio_df["Data de Validade"] = pd.to_datetime(relatorio_df["Data de Validade"]).dt.strftime('%d/%m/%Y')
            st.dataframe(relatorio_df)
        else:
            st.info("Nenhum consumo registrado ainda.")

        # Verificar vencimentos em até 7 dias
        hoje = datetime.today().date()
        data_limite = hoje + timedelta(days=7)

        atas_vencendo = [ata for ata in atas_data.values() if ata["data_validade"] and pd.to_datetime(ata["data_validade"]).date() <= data_limite]

        if atas_vencendo:
            st.warning("Alertas de vencimento de atas nos próximos 7 dias:")
            for ata in sorted(atas_vencendo, key=lambda x: x["data_validade"]):
                validade = pd.to_datetime(ata["data_validade"]).strftime('%d/%m/%Y')
                st.write(f"**Ata:** {ata['nome']} — **Validade:** {validade}")
        else:
            st.info("Nenhuma Ata vencendo em 7 dias.")
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")
