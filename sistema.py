import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import streamlit.components.v1 as components
from supabase import create_client, Client

# Conectar ao Supabase
SUPABASE_URL = "https://btstungeitzcizcysupd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJ0c3R1bmdlaXR6Y2l6Y3lzdXBkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQwNjAxNTUsImV4cCI6MjA1OTYzNjE1NX0.L1KZfGO_9Cq7iOGtdDVD4bGp02955s65fjcK2I1jntc"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Alterando o nome da página e o ícone
st.set_page_config(page_title= "Gestão de ARP", 
                   page_icon= "📄", 
                   layout = "wide")

st.title("Sistema de Gestão de Atas de Registro de Preços")
st.write("Bem-vindo ao sistema de controle de atas, onde você pode gerenciar saldos, acompanhar validade das atas e visualizar relatórios.")

# Estabelecendo o layout com abas
tabs = st.tabs(["Fornecedores", "Atas", "Empenhos", "Histórico de Empenhos", "Relatórios"])

# Identificando o tema
modo_tema = st.get_option("theme.base")

# Fornecedores -----------------------------------------------------------------------------------------------------------------
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

    # Edição e Exclusão de fornecedores:
    st.header("Editar ou Excluir Fornecedor")

    try:
        response = supabase.table("fornecedores").select("id, nome").order("nome").execute()
        fornecedores_data = response.data
        fornecedores_dict = {f["nome"]:f["id"] for f in fornecedores_data}
        fornecedores_nomes =  ["Selecione"] + list(fornecedores_dict.keys())

        fornecedor_selecionado = st.selectbox("Escolha um fornecedor para editar ou excluir", fornecedores_nomes)

        if fornecedor_selecionado != "Selecione":
            fornecedor_id = fornecedores_dict[fornecedor_selecionado]

            fornecedor_info_response = supabase.table("fornecedores").select("*").eq("id", fornecedor_id).single().execute()
            fornecedor_info = fornecedor_info_response.data

            with st.form("form_editar_fornecedor"):
                novo_nome = st.text_input("Nome do Fornecedor", value=fornecedor_info["nome"])
                novo_cnpj = st.text_input("CNPJ", value=fornecedor_info["cnpj"])
                novo_email = st.text_input("E-mail", value=fornecedor_info["email"])
                novo_endereco = st.text_input("Endereço", value=fornecedor_info["endereco"])
                novo_telefone = st.text_input("Telefone", value=fornecedor_info["telefone"])

                col1, col2 = st.columns(2)    
                atualizar = col1.form_submit_button("Atualizar Fornecedor", icon=":material/edit:")
                excluir = col2.form_submit_button("Excluir Fornecedor", icon=":material/delete:")

                if atualizar:
                    try:
                        supabase.table("fornecedores").update({
                            "nome": novo_nome,
                            "cnpj": novo_cnpj,
                            "email": novo_email,
                            "endereco": novo_endereco,
                            "telefone": novo_telefone
                        }).eq("id", fornecedor_id).execute()

                        st.success(f"Fornecedor {novo_nome} atualizado com sucesso!")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar fornecedor: {e}")
                
                if excluir:
                    confirmar = st.checkbox("Confirmo que desejo excluir este fornecedor.")

                    if confirmar:
                        try:
                            supabase.table("fornecedores").delete().eq("id", fornecedor_id).execute()
                            st.sucess("Fornecedor excluído com sucesso!")
                            st.experimental_rerun()

                        except Exception as e:
                            st.error(f"Erro ao excluir fornecedor: {e}")
                    else:
                        st.warning("Marque a caixa de confirmação para excluir o fornecedor.")


    except Exception as e:
        st.error(f"Erro ao carregar fornecedores: {e}")


# Atas -----------------------------------------------------------------------------------------------------------------------
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
    st.header("Visualizar Atas Cadastradas")

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

    # Editar ou Excluir Ata/Equipamento
    st.header("Editar ou Excluir Ata")

    try:
        response_atas = supabase.table("atas").select("id,nome").order("nome").execute() 
        atas_data = response_atas.data
        atas_dict = {a["nome"]: a["id"] for a in atas_data}
        atas_nomes = ["Selecione"] + list(atas_dict.keys())

        ata_selecionada = st.selectbox("Selecione a Ata", atas_nomes)

        if ata_selecionada != "Selecione":
            ata_id = atas_dict[ata_selecionada]
            ata_info_response = supabase.table("atas").select("*").eq("id", ata_id).single().execute()
            ata_info = ata_info_response.data

            response_fornecedores = supabase.table("fornecedores").select("id,nome").order("nome").execute()
            fornecedores_data = response_fornecedores.data
            fornecedores_dict = {f["nome"]: f["id"] for f in fornecedores_data}
            fornecedores_nomes = list(fornecedores_dict.keys())

            nome_fornecedor_atual = next((nome for nome, id_ in fornecedores_dict.items() if id_ == ata_info["fornecedor_id"]), None)

            with st.form("form_editar_ata"):
                novo_nome = st.text_input("Nome da Ata", value=ata_info["nome"])
                
                nova_data = st.date_input("Data da Ata", format="DD/MM/YYYY", value=pd.to_datetime(ata_info["data_inicio"]).date())

                nova_validade_ata = st.date_input("Validade da Ata", min_value=nova_data, format="DD/MM/YYYY", value=pd.to_datetime(ata_info["data_validade"]).date())

                novo_fornecedor_nome = st.selectbox("Fornecedor", fornecedores_nomes,key="selecione_novo_fornecedor_nome", index=fornecedores_nomes.index(nome_fornecedor_atual))

                novo_link_ata = st.text_input("Link para o PDF da Ata", value=ata_info["link_ata"])

                col1, col2 = st.columns(2)
                atualizar = col1.form_submit_button("Editar Ata", icon=":material/edit:")
                excluir = col2.form_submit_button("Excluir Ata", icon=":material/delete:")

            if atualizar:
                try:
                    novo_fornecedor_id = fornecedores_dict[novo_fornecedor_nome]

                    supabase.table("atas").update({
                        "nome": novo_nome,
                        "data_inicio": nova_data.isoformat(),
                        "data_validade": nova_validade_ata.isoformat(),
                        "fornecedor_id": novo_fornecedor_id,
                        "link_ata": novo_link_ata
                    }).eq("id", ata_id).execute()

                    st.success("Ata atualizada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao atualizar a Ata: {e}")

            if excluir:
                try:
                    supabase.table("atas").delete().eq("id", ata_id).execute()
                    st.success("Ata excluída com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao excluir a Ata: {e}")
            

            # Buscar equipamentos vinculados à Ata
            st.subheader("Equipamentos desta Ata")
            st.write("Clique no equipamento que deseja editar ou excluir.")
        
            response_equip = supabase.table("equipamentos").select("*").eq("ata_id", ata_id).execute()
            equipamentos = response_equip.data

            if not equipamentos:
                st.info("Nenhum equipamento cadastrado para essa Ata.")
            else:
                for equipamento in equipamentos:
                    with st.expander(f"Equipamento: {equipamento['especificacao']}"):
                        with st.form(f"form_equip_{equipamento['id']}"):
                            nova_especificacao = st.text_input("Especificação", value=equipamento["especificacao"])
                            nova_marca_modelo = st.text_input("Marca/Modelo", value=equipamento["marca_modelo"])
                            nova_qtd = st.number_input("Quantidade", value=equipamento["quantidade"], step=1)
                            novo_saldo = st.number_input("Saldo Disponível", value=equipamento["saldo_disponivel"], step=1)
                            novo_valor_unit = st.number_input("Valor Unitário (R$)", value=float(equipamento["valor_unitario"]), step=0.01, format="%.2f")
                            
                            # Valor total calculado automaticamente
                            valor_total = nova_qtd * novo_valor_unit
                            st.text(f"Valor Total: R$ {valor_total:.2f}")

                            col1, col2 = st.columns(2)
                            atualizar = col1.form_submit_button("Editar Equipamento", icon=":material/edit:")
                            excluir = col2.form_submit_button("Excluir Equipamento", icon=":material/delete:")

                        if atualizar:
                            try:
                                supabase.table("equipamentos").update({
                                    "especificacao": nova_especificacao,
                                    "marca_modelo": nova_marca_modelo,
                                    "quantidade": nova_qtd,
                                    "saldo_disponivel": novo_saldo,
                                    "valor_unitario": novo_valor_unit,
                                    "valor_total": valor_total
                                }).eq("id", equipamento["id"]).execute()
                                st.success(f"Equipamento '{nova_especificacao}' atualizado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao atualizar equipamento: {e}")

                        if excluir:
                            try:
                                supabase.table("equipamentos").delete().eq("id", equipamento["id"]).execute()
                                st.success(f"Equipamento '{equipamento['especificacao']}' excluído com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao excluir equipamento: {e}")
    except Exception as e:
        st.error(f"Erro ao carregar equipamentos: {e}")

# Empenhos -----------------------------------------------------------------------------------------------------------------                
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
                for emp in empenhos:
                    with st.expander(f"Empenho de {emp['quantidade_empenhada']}x {emp['especificacao']} em {pd.to_datetime(emp['data_empenho']).strftime('%d/%m/%Y')}"):
                        with st.form(f"form_emp_{emp['id']}"):
                            nova_quantidade = st.number_input("Quantidade", min_value=1, value=emp["quantidade_empenhada"], key=f"qtd_{emp['id']}")
                            nova_data = st.date_input("Data do Empenho", format="DD/MM/YYYY",value=pd.to_datetime(emp["data_empenho"]).date(), key=f"data_{emp['id']}")
                            nova_obs = st.text_input("Observação", value=emp["observacao"] or "", key=f"obs_{emp['id']}")

                            col1, col2 = st.columns(2)
                            atualizar = col1.form_submit_button("Editar Empenho", icon=":material/edit:")
                            excluir = col2.form_submit_button("Excluir Empenho", icon=":material/delete:")

                        if atualizar:
                            try:
                                supabase.table("empenhos").update({
                                    "quantidade_empenhada": nova_quantidade,
                                    "data_empenho": nova_data.isoformat(),
                                    "observacao": nova_obs
                                }).eq("id", emp["id"]).execute()
                                st.success("Empenho atualizado com sucesso.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Erro ao atualizar empenho: {e}")
                        if excluir:
                            try:
                                supabase.table("empenhos").delete().eq("id", emp["id"]).execute()
                                st.success("Empenho excluído com sucesso.")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error(f"Erro ao excluir empenho: {e}")

            else:
                st.info("Nenhum empenho registrado para esta Ata.")
        except Exception as e:
            st.error(f"Erro ao buscar empenhos: {e}")

# Histórico de Empenhos -----------------------------------------------------------------------------------------------------------------
with tabs[3]:
    st.header("Histórico de Empenhos")

    try:
        # Filtrar por ata
        atas_response = supabase.table("atas").select("id, nome").order("nome").execute()
        atas_data = atas_response.data
        atas_dict = {ata["nome"]: ata["id"] for ata in atas_data}
        atas_opcoes = ["Todas"] + list(atas_dict.keys())
        ata_filtro = st.selectbox("Filtrar por Ata", atas_opcoes, key="selecione_ata_filtro")

        # Filtrar por equipamento
        equipamentos_response = supabase.table("equipamentos").select("id, especificacao, ata_id").execute()
        equipamentos_data = equipamentos_response.data
        equipamentos_dict = {eq["id"]: eq for eq in equipamentos_data}
        equipamentos_opcoes = ["Todos"] + sorted(list(set(eq["especificacao"] for eq in equipamentos_data)))
        equipamento_filtro = st.selectbox("Filtrar por Equipamento", equipamentos_opcoes, key="filtro_equipamento")

        # Filtro de data
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data inicial", value=pd.to_datetime("2023-01-01"), format= 'DD/MM/YYYY', key="data_inicio")
        with col2:
            data_fim = st.date_input("Data final", value=pd.to_datetime("today"), format= 'DD/MM/YYYY', key="data_fim")

        # Buscar empenhos
        empenhos_response = supabase.table("empenhos").select("*").order("data_empenho", desc=True).execute()
        empenhos_data = empenhos_response.data

        empenhos_filtrados = []
        for emp in empenhos_data:
            equipamento = equipamentos_dict.get(emp["equipamento_id"])
            if not equipamento:
                continue

            ata_id = equipamento["ata_id"]
            ata_nome = next((nome for nome, id_ in atas_dict.items() if id_ == ata_id), "Desconhecida")
            especificacao = equipamento["especificacao"]
            data_empenho = pd.to_datetime(emp["data_empenho"])

            # Aplicar filtros
            if ata_filtro != "Todas" and atas_dict[ata_filtro] != ata_id:
                continue
            if equipamento_filtro != "Todos" and especificacao != equipamento_filtro:
                continue
            if not (data_inicio <= data_empenho.date() <= data_fim):
                continue

            empenhos_filtrados.append({
                "Ata": ata_nome,
                "Equipamento": especificacao,
                "Quantidade": emp["quantidade_empenhada"],
                "Data do Empenho": data_empenho.strftime('%d/%m/%Y'),
                "Observação": emp["observacao"]
            })

        if empenhos_filtrados:
            df_empenhos = pd.DataFrame(empenhos_filtrados)
            st.dataframe(df_empenhos)

            st.markdown("## 📊 Análises e Gráficos")

            # Resumos
            total_empenhos = len(df_empenhos)
            quantidade_total = df_empenhos["Quantidade"].sum()
            total_atas = df_empenhos["Ata"].nunique()

            col1, col2, col3 = st.columns(3)

            # Cores para light e dark
            if modo_tema == "dark":
                bg_color = "#1e1e1e"
                text_color = "#f0f0f0"
                number_color = "#4fc3f7"  # Azul clarinho
            else:
                bg_color = "#f0f2f6"
                text_color = "#333333"
                number_color = "#004aad"  # Azul escuro

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                    <div style="background-color:{bg_color};padding:20px;border-radius:15px;
                                text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.05);">
                        <h4 style="margin:0;color:{text_color};">Total de Empenhos</h4>
                        <h2 style="margin:0;color:{number_color};">{total_empenhos}</h2>
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                    <div style="background-color:{bg_color};padding:20px;border-radius:15px;
                                text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.05);">
                        <h4 style="margin:0;color:{text_color};">Quantidade Total Empenhada</h4>
                        <h2 style="margin:0;color:{number_color};">{quantidade_total}</h2>
                    </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                    <div style="background-color:{bg_color};padding:20px;border-radius:15px;
                                text-align:center;box-shadow:0 4px 8px rgba(0,0,0,0.05);">
                        <h4 style="margin:0;color:{text_color};">Atas Envolvidas</h4>
                        <h2 style="margin:0;color:{number_color};">{total_atas}</h2>
                    </div>
                """, unsafe_allow_html=True)


            aba1, aba2, aba3 = st.tabs(["📊 Por Ata", "📈 Por Mês", "🔧 Por Equipamento"])

            with aba1:
                total_por_ata = df_empenhos.groupby("Ata")["Quantidade"].sum().reset_index()
                fig_ata = px.bar(total_por_ata, x="Ata", y="Quantidade", title="Total de Empenhos por Ata", text_auto=True)
                st.plotly_chart(fig_ata, use_container_width=True)

            with aba2:
                df_empenhos["Data do Empenho"] = pd.to_datetime(df_empenhos["Data do Empenho"]).dt.date
                st.write(df_empenhos)
                df_empenhos["AnoMes"] = df_empenhos["Data do Empenho"].dt.to_period("M").astype(str)
                quantidade_mensal = df_empenhos.groupby("AnoMes")["Quantidade"].sum().reset_index()
                fig_mensal = px.line(quantidade_mensal, x="AnoMes", y="Quantidade", markers=True,
                                    title="Quantidade Empenhada por Mês")
                st.plotly_chart(fig_mensal, use_container_width=True)

            with aba3:
                top_eq = df_empenhos.groupby("Equipamento")["Quantidade"].sum().nlargest(5).reset_index()
                fig_top_eq = px.bar(top_eq, x="Quantidade", y="Equipamento", orientation="h",
                                    title="Top 5 Equipamentos Mais Empenhados", text_auto=True)
                st.plotly_chart(fig_top_eq, use_container_width=True)

        else:
            st.info("Nenhum empenho encontrado com os filtros selecionados.")
    except Exception as e:
        st.error(f"Erro ao buscar empenhos: {e}")



# Relatórios de Consumo e Status -----------------------------------------------------------------------------------------------------------------
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
