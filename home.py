import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
import streamlit.components.v1 as components
from db import supabase
import textwrap
import re
from dateutil.relativedelta import relativedelta

def show_home():
    caminho_css = "style/main.css"
    with open(caminho_css) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    usuario = st.session_state.get("usuario", {})

    col1, col2 = st.columns([8, 2])
    with col1:
        st.markdown(
            f"""<p style='margin-bottom:0;'><strong>HC-UFU - Hospital de Clínicas de Uberlândia</strong></p>
            <p style='margin-top:0;'>Bem-vindo(a), {usuario.get('email', 'usuário')}</p>""",
            unsafe_allow_html=True
        )
    with col2:
        if st.button("🚪 Encerrar sessão"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Cabeçalho
    with st.container():
        st.markdown('<div class="fixed-header">', unsafe_allow_html=True)
        col1, col2 = st.columns([1,5])
        with col1:
            st.image('assets/logo-sigah.svg', width=300)
        with col2:
            st.html("<div class='header-title'>Sistema Integrado de Gestão de Atas Hospitalares</div>")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("Bem-vindo ao SIGAH, um sistema especializado no controle de atas, onde você pode gerenciar saldos, acompanhar validade das atas e visualizar relatórios.")


    # Funções para formatação
    def formatar_moeda(valor):
        try:
            valor_float = float(str(valor).replace(',', '.'))
            return f"R$ {valor_float:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        except:
            return valor


    def formatar_telefone(numero: str) -> str:
        """Formata um número de telefone brasileiro"""
        numero_limpo = re.sub(r'\D', '', numero)  # Remove tudo que não for dígito

        if len(numero_limpo) == 11:
            # Com DDD + celular (ex: 34991234567)
            return f"({numero_limpo[:2]}) {numero_limpo[2:7]}-{numero_limpo[7:]}"
        elif len(numero_limpo) == 10:
            # Com DDD + fixo (ex: 3421234567)
            return f"({numero_limpo[:2]}) {numero_limpo[2:6]}-{numero_limpo[6:]}"
        elif len(numero_limpo) == 9:
            # Celular sem DDD (ex: 991234567)
            return f"{numero_limpo[:5]}-{numero_limpo[5:]}"
        elif len(numero_limpo) == 8:
            # Fixo sem DDD (ex: 21234567)
            return f"{numero_limpo[:4]}-{numero_limpo[4:]}"
        else:
            return numero  # Retorna como veio se não bater com formatos esperados

    def get_config(chave):
        configuracoes = supabase.table('configuracoes').select("valor").eq("chave", chave).execute()
        if configuracoes.data:
            return int(configuracoes.data[0]["valor"])
    
    def update_config(chave, valor):
        resp = supabase.table("configuracoes").upsert({
            "chave": chave,
            "valor": int(valor)
        }).execute()
 
    def validar_dados_fornecedor(nome, cnpj, cep):
        padrao_cnpj = r"^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$"
        padrao_cep = r"\d{5}-\d{3}"

        if not nome or not cnpj:
            return False, "Preencha todos os campos obrigatórios."
        elif not re.match(padrao_cnpj, cnpj):
            return False, "❌ CNPJ inválido. Use o formato 00.000.000/0000-00."
        elif cep and not re.fullmatch(padrao_cep, cep):
            return False, "❌ CEP inválido. Use o formato 00000-000."
        return True, ""

    def formatar_dados_fornecedor(nome, telefone, endereco):
        nome_formatado = ' '.join(nome.split()).upper()
        endereco_formatado = ' '.join(endereco.split()).upper()
        telefone_formatado = formatar_telefone(telefone)
        return nome_formatado, telefone_formatado, endereco_formatado

    def cnpj_existe(cnpj):
        resultado = supabase.table("fornecedores").select("id").eq("cnpj", cnpj).execute()
        return bool(resultado.data)

    def cadastrar_fornecedor(dados):
        supabase.table("fornecedores").insert(dados).execute()

    def buscar_fornecedores(colunas=None):
        colunas_str = ", ".join(colunas) if colunas else "*"
        return supabase.table("fornecedores").select(colunas_str).order("nome").execute().data

    def buscar_fornecedor_por_id(fornecedor_id):
        return supabase.table("fornecedores").select("*").eq("id", fornecedor_id).single().execute().data

    def excluir_fornecedor(fornecedor_id):
        supabase.table("fornecedores").delete().eq("id", fornecedor_id).execute()
    
    def listar_nomes_ids_fornecedores():
        response = supabase.table("fornecedores").select("id, nome").order("nome").execute()
        return response.data

    def buscar_detalhes_fornecedor(fornecedor_id):
        response = supabase.table("fornecedores").select("*").eq("id", fornecedor_id).single().execute()
        return response.data

    def atualizar_dados_fornecedor(fornecedor_id, nome, cnpj, email, endereco, cep, telefone):
        nome_formatado = ' '.join(nome.split()).upper()
        endereco_formatado = ' '.join(endereco.split()).upper()
        telefone_formatado = formatar_telefone(telefone)

        supabase.table("fornecedores").update({
            "nome": nome_formatado,
            "cnpj": cnpj,
            "email": email,
            "endereco": endereco_formatado,
            "cep": cep,
            "telefone": telefone_formatado
        }).eq("id", fornecedor_id).execute()

    def listar_todos_fornecedores():
        response = supabase.table("fornecedores").select("*").order("nome").execute()
        return response.data

    def excluir_fornecedor(fornecedor_id):
        supabase.table("fornecedores").delete().eq("id", fornecedor_id).execute()

    def formatar_dados_para_df(dados):
        df = pd.DataFrame(dados).drop(columns=["id"])
        df = df.rename(columns={
            "nome": "Nome",
            "cnpj": "CNPJ",
            "email": "E-mail",
            "endereco": "Endereço",
            "cep": "CEP",
            "telefone": "Telefone"
        })
        return df
    
    def cadastrar_ata(num_ata, data_ata, validade_ata, fornecedor_exibido, link_ata, categoria_ata, ata_renovavel, renovavel_bool):
        if num_ata and data_ata and ata_renovavel and validade_ata and categoria_ata and (fornecedor_exibido != "Selecione"):
            if re.fullmatch(r'\d{1,5}/\d{4}', num_ata):
                try:
                    fornecedor_id = fornecedores_dict[fornecedor_exibido]

                    supabase.table("atas").insert({
                        "nome": num_ata,
                        "data_inicio": data_ata.isoformat(),
                        "data_validade": validade_ata.isoformat(),
                        "fornecedor_id": fornecedor_id,
                        "link_ata": link_ata,
                        "categoria_ata": categoria_ata,
                        "ata_renovavel": renovavel_bool,
                    }).execute()
                    st.success(f"Ata '{num_ata}' cadastrada com sucesso!")
                    st.session_state["nome"] = ""
                    st.session_state["data_inicio"] = ""
                    st.session_state["data_validade"] = ""
                    st.session_state["fornecedor_id"] = ""
                    st.session_state["link_ata"] = ""
                    st.session_state["categoria_ata"] = ""
                    st.session_state["ata_renovavel"] = ""

                except Exception as e:
                    st.error(f"Erro ao cadastrar a Ata: {e}")
            else:
                st.error("Formato inválido. Use o padrão: 1234/2024")   
        else:
            st.warning("Preencha todos os campos obrigatórios.")

    def buscar_atas(colunas=None):
        colunas_str = ", ".join(colunas) if colunas else "*"
        return supabase.table("atas").select(colunas_str).order("nome").execute().data
    
    def cadastrar_equipamento(especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario):
        if especificacao and marca_modelo and quantidade and saldo_disponivel and valor_unitario:
            try:
                espeficicacao_formatada = ' '.join(especificacao.split()).upper()
                marca_modelo_formatada = ' '.join(marca_modelo.split()).upper()
                supabase.table("equipamentos").insert({
                    "ata_id": ata_id,
                    "especificacao": espeficicacao_formatada,
                    "marca_modelo": marca_modelo_formatada,
                    "quantidade": quantidade,
                    "saldo_disponivel": saldo_disponivel,
                    "valor_unitario": valor_unitario,
                    "valor_total": valor_total
                }).execute()
                st.success(f"Equipamento '{espeficicacao_formatada}' cadastrado com sucesso na ata '{ata_nome}'!")
            except Exception as e:
                st.error(f"Erro ao cadastrar equipamento: {e}")
        else:
            st.warning("Preencha todos os campos obrigatórios.")

    # Estabelecendo o layout com abas
    tabs = st.tabs(["Fornecedores", "Atas", "Empenhos", "Histórico Geral de Empenhos", "Relatórios de Consumo e Status", "Renovação de Atas"])

    # Fornecedores -----------------------------------------------------------------------------------------------------------------
    with tabs[0]:
        col1, col2 = st.columns([1, 4])

        # Sessão de estado para armazenar aba ativa
        if "aba_fornecedores" not in st.session_state:
            st.session_state.aba_fornecedores = "Cadastrar"

        botoes_fornecedores = ["Cadastrar", "Consultar", "Atualizar", "Excluir"]
        with col1:
            st.image("assets/logos.svg", width=300)
            for b in botoes_fornecedores:
                if st.button(b, key=f"botao_{b}_fornecedores"):
                    st.session_state.aba_fornecedores = b

        with col2:
            aba = st.session_state.aba_fornecedores

            if aba == "Cadastrar":
                st.subheader("Cadastro de Fornecedores")
                with st.form("novo_fornecedor"):
                    nome_fornecedor = st.text_input("Nome do Fornecedor")
                    cnpj = st.text_input("CNPJ (formato: 00.000.000/0000-00)")
                    email = st.text_input("E-mail")
                    endereco = st.text_input("Endereço")
                    cep = st.text_input("CEP (formato = 00000-000)", max_chars=9)
                    telefone = st.text_input("Telefone")
                    submit = st.form_submit_button("Cadastrar Fornecedor")

                if submit:
                    valido, msg = validar_dados_fornecedor(nome_fornecedor, cnpj, cep)
                    if not valido:
                        st.error(msg)
                        return
                    
                    if cnpj_existe(cnpj):
                        st.warning("⚠️ Já existe um fornecedor cadastrado com esse CNPJ.")
                        return
                    
                    try:
                        nome_formatado, telefone_formatado, endereco_formatado = formatar_dados_fornecedor(
                            nome_fornecedor, telefone, endereco)
                        
                        dados = {
                            "nome": nome_formatado,
                            "cnpj": cnpj,
                            "email": email,
                            "endereco": endereco_formatado,
                            "cep": cep,
                            "telefone": telefone_formatado
                        }
                        cadastrar_fornecedor(dados)
                        st.success(f"Fornecedor '{nome_formatado}' cadastrado com sucesso!")
                        st.session_state["nome_fornecedor"] = ""
                        st.session_state["cnpj"] = ""
                        st.session_state["email"] = ""
                        st.session_state["endereco"] = ""
                        st.session_state["cep"] = ""
                        st.session_state["telefone"] = ""

                    except Exception as e:
                        st.error(f"Erro ao cadastrar fornecedor: {e}")

            elif aba == "Consultar":
                st.subheader("Fornecedores Cadastrados")
                try:
                    fornecedores_result = buscar_fornecedores()

                    if fornecedores_result:
                        df_fornecedores = pd.DataFrame(fornecedores_result)
                        df_fornecedores = df_fornecedores.rename(columns={
                            "nome": "Nome",
                            "cnpj": "CNPJ",
                            "email": "E-mail",
                            "endereco": "Endereço",
                            "cep": "CEP",
                            "telefone": "Telefone"
                        })
                        st.dataframe(df_fornecedores, height=300)
                    else:
                        st.info("Nenhum fornecedor cadastrado.")
                except Exception as e:
                    st.error(f"Erro ao buscar fornecedor: {e}")

            elif aba == "Atualizar":
                    st.subheader("Atualizar Fornecedor")
                    try:
                        fornecedores_data = listar_nomes_ids_fornecedores()
                        fornecedores_dict = {f["nome"]: f["id"] for f in fornecedores_data}
                        fornecedores_nomes = ["Selecione"] + list(fornecedores_dict.keys())

                        fornecedor_selecionado = st.selectbox("Escolha um fornecedor", fornecedores_nomes)

                        if fornecedor_selecionado != "Selecione":
                            fornecedor_id = fornecedores_dict[fornecedor_selecionado]
                            fornecedor_info = buscar_detalhes_fornecedor(fornecedor_id)

                            if fornecedor_info:
                                with st.form("form_editar_fornecedor"):
                                    novo_nome = st.text_input("Nome do Fornecedor", value=fornecedor_info["nome"])
                                    novo_cnpj = st.text_input("CNPJ", value=fornecedor_info["cnpj"])
                                    novo_email = st.text_input("E-mail", value=fornecedor_info["email"])
                                    novo_endereco = st.text_input("Endereço", value=fornecedor_info["endereco"])
                                    novo_cep = st.text_input("CEP", value=fornecedor_info["cep"])
                                    novo_telefone = st.text_input("Telefone", value=fornecedor_info["telefone"])

                                    atualizar = st.form_submit_button("Atualizar Fornecedor")

                                    if atualizar:
                                        valido, msg = validar_dados_fornecedor(novo_nome, novo_cnpj, novo_cep)
                                        if not valido:
                                            st.error(msg)
                                            return
                                        
                                        try:
                                            atualizar_dados_fornecedor(
                                                fornecedor_id,
                                                nome=novo_nome,
                                                cnpj=novo_cnpj,
                                                email=novo_email,
                                                endereco=novo_endereco,
                                                cep=novo_cep,
                                                telefone=novo_telefone
                                            )
                                            st.success(f"Fornecedor {novo_nome.upper()} atualizado com sucesso!")
                                            st.session_state["novo_nome"] = ""
                                            st.session_state["novo_cnpj"] = ""
                                            st.session_state["novo_email"] = ""
                                            st.session_state["novo_endereco"] = ""
                                            st.session_state["novo_cep"] = ""
                                            st.session_state["novo_telefone"] = ""

                                        except Exception as e:
                                            st.error(f"Erro ao atualizar fornecedor: {e}")
                    except Exception as e:
                        st.error(f"Erro ao carregar fornecedores: {e}")

            elif aba == "Excluir":
                st.subheader("Excluir Fornecedor")
                try:
                    fornecedores_data = listar_todos_fornecedores()
                    fornecedores_dict = {f["nome"]: f["id"] for f in fornecedores_data}
                    fornecedores_nomes = ["Selecione"] + list(fornecedores_dict.keys())

                    fornecedor_selecionado = st.selectbox("Escolha um fornecedor", fornecedores_nomes)

                    if fornecedor_selecionado != "Selecione":
                        fornecedor_id = fornecedores_dict[fornecedor_selecionado]
                        fornecedor_info = next((f for f in fornecedores_data if f["id"] == fornecedor_id), None)

                        if fornecedor_info:
                            fornecedor_df = formatar_dados_para_df([fornecedor_info])
                            st.dataframe(fornecedor_df)

                            with st.form("botao_excluir_fornecedor", border=False):
                                confirmar = st.checkbox("Confirmo que desejo excluir este fornecedor.")
                                excluir = st.form_submit_button("Excluir Fornecedor")

                            if excluir:
                                if confirmar:
                                    try:
                                        excluir_fornecedor(fornecedor_id)
                                        st.success("Fornecedor excluído com sucesso!")
                                    except Exception as e:
                                        st.error(f"Erro ao excluir fornecedor: {e}")
                                else:
                                    st.warning("Você precisa confirmar antes de excluir.")
                except Exception as e:
                    st.error(f"Erro ao carregar fornecedores: {e}")


    # Atas -----------------------------------------------------------------------------------------------------------------------
    with tabs[1]:
        col1, col2 = st.columns([1, 4])

        # Sessão de estado para armazenar aba ativa
        if "aba_atas" not in st.session_state:
            st.session_state.aba_atas = "Cadastrar"

        with col1:
            st.image("assets/logos.svg", width=300)
            botoes_atas = ["Cadastrar", "Consultar", "Atualizar", "Excluir"]
            for b in botoes_atas:
                if st.button(b, key=f"botao_{b}_ata"):
                    st.session_state.aba_atas = b
        
        with col2:
            aba = st.session_state.aba_atas

            if aba == "Cadastrar":
                st.subheader("Cadastro de Atas")
                try:
                    fornecedores_result = buscar_fornecedores(["id", "nome", "cnpj"])

                    # Exibir no selectbox como "Nome (CNPJ)"
                    fornecedores_dict = {
                        f"{f['nome']} ({f['cnpj']})": f["id"]
                        for f in fornecedores_result
                    }

                    fornecedores_cadastrados = ["Selecione"] + list(fornecedores_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar fornecedores: {e}")
                    fornecedores_cadastrados = ["Selecione"]
                    fornecedores_dict = {}

                # Formulário para cadastrar nova Ata
                with st.form("nova_ata"):
                    num_ata = st.text_input("Número da Ata (ex: 12/2024, 1234/2025)")
                    data_ata = st.date_input("Data da Ata", format="DD/MM/YYYY")
                    validade_ata = st.date_input("Validade da Ata", min_value=data_ata, format="DD/MM/YYYY")
                    fornecedor_exibido = st.selectbox("Fornecedor", fornecedores_cadastrados, key="selecione_fornecedor_nome", help="Digite o nome ou CNPJ para localizar o fornecedor.")
                    categoria_ata = st.selectbox("Categoria", ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"], key="selecione_categoria_ata")
                    link_ata = st.text_input("Número do Protocolo SEI")
                    ata_renovavel = st.radio("Ata renovável?", options=["Sim", "Não"], horizontal=True)
                    renovavel_bool = ata_renovavel == "Sim"

                    submit_ata = st.form_submit_button("Cadastrar Ata")

                    if submit_ata:
                        cadastrar_ata(num_ata, data_ata, validade_ata, fornecedor_exibido, link_ata, categoria_ata, ata_renovavel, renovavel_bool)

                # Adicionar Equipamento na Ata --------------------------------------------
                st.subheader("Adicionar Equipamento à Ata")

                try:
                    atas_result = buscar_atas(["id", "nome"])
                    atas_dict = {a["nome"]: a["id"] for a in atas_result}
                    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar atas: {e}")
                    atas_cadastradas = ["Selecione"]
                    atas_dict = {}

                ata_nome = st.selectbox("Selecione a Ata", atas_cadastradas, key="selecione_ata_nome")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]

                    with st.form("novo_equipamento"):
                        especificacao = st.text_input("Especificação")
                        marca_modelo = st.text_input("Marca/Modelo")
                        quantidade = st.number_input("Quantidade", min_value=1, step=1)
                        saldo_disponivel = st.number_input("Saldo disponível", min_value=0, step=1)
                        valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f")
                        valor_total = valor_unitario * quantidade

                        submit_equipamento = st.form_submit_button("Adicionar Equipamento")

                        if submit_equipamento:
                            cadastrar_equipamento(especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario)
                        

            elif aba == "Consultar":
                st.subheader("Consultar Atas Cadastradas")

                try:
                    # Buscar todas as atas com nome do fornecedor
                    atas_result = buscar_atas()
                    atas_dict = {a["nome"]: a["id"] for a in atas_result}
                    atas_opcoes = ["Selecione"] + list(atas_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar atas: {e}")
                    atas_opcoes = ["Selecione"]
                    atas_dict = {}

                ata_visualizar = st.selectbox("Selecione uma Ata para consultar", atas_opcoes, key="selecione_ata_visualizar")

                if ata_visualizar != "Selecione":
                    ata_id = atas_dict[ata_visualizar]

                    # Buscar os dados da Ata selecionada
                    ata_info = next((a for a in atas_result if a["id"] == ata_id), None)

                    if ata_info:
                        nome = ata_info["nome"]
                        data_ata = ata_info["data_inicio"]
                        validade_ata = ata_info["data_validade"]
                        categoria_ata = ata_info["categoria_ata"]
                        link_ata = ata_info.get("link_ata", "")
                        fornecedor_nome = ata_info["fornecedores"]["nome"]
                        ata_renovavel_bool = ata_info["ata_renovavel"]

                        st.markdown(f"**Número:** {nome}")
                        st.markdown(f"**Data da Ata:** {pd.to_datetime(data_ata).strftime('%d/%m/%Y')}")
                        st.markdown(f"**Validade:** {pd.to_datetime(validade_ata).strftime('%d/%m/%Y')}")
                        st.markdown(f"**Fornecedor:** {fornecedor_nome}")
                        st.markdown(f"**Categoria:** {categoria_ata}")
                        st.markdown(f"**N° Protocolo SEI:** {link_ata}")
                        st.markdown(f"**Ata renovável?**: {'Sim' if ata_renovavel_bool else 'Não'}")

                        # Buscar os equipamentos dessa ata
                        try:
                            response = supabase.table("equipamentos").select(
                                "especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario, valor_total"
                            ).eq("ata_id", ata_id).execute()
                            equipamentos = response.data

                            st.subheader("Equipamentos desta Ata")

                            if equipamentos:
                                df_equip = pd.DataFrame(equipamentos)
                                df_equip["valor_unitario"] = df_equip["valor_unitario"].apply(formatar_moeda)
                                df_equip["valor_total"] = df_equip["valor_total"].apply(formatar_moeda)


                                df_equip = df_equip.rename(columns={
                                    "especificacao": "Especificação",
                                    "marca_modelo": "Marca/Modelo",
                                    "quantidade": "Quantidade",
                                    "saldo_disponivel": "Saldo Disponível",
                                    "valor_unitario": "Valor Unitário",
                                    "valor_total": "Valor Total"
                                })
                                st.dataframe(df_equip, height=200)
                            else:
                                st.info("Nenhum equipamento cadastrado para esta Ata.")
                        except Exception as e:
                            st.error(f"Erro ao buscar equipamentos: {e}")

            elif aba == "Atualizar":
                st.subheader("Atualizar dados de uma Ata")

                atas_data = buscar_atas(["id", "nome"])
                atas_dict = {a["nome"]: a["id"] for a in atas_data}
                atas_nomes = ["Selecione"] + list(atas_dict.keys())

                ata_selecionada = st.selectbox("Selecione uma Ata para atualizar dados", atas_nomes)

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
                        nova_categoria_ata = st.selectbox("Categoria", ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"], key="selecione_categoria_ata")
                        novo_link_ata = st.text_input("Número do Protocolo SEI", value=ata_info["link_ata"])
                        nova_info_renovacao = st.radio("Ata renovável?", options=["Sim", "Não"], horizontal=True)
                        nova_info_renovacao_bool = nova_info_renovacao == 'Sim'

                        atualizar = st.form_submit_button("Atualizar Ata")

                    if atualizar:
                        try:
                            novo_fornecedor_id = fornecedores_dict[novo_fornecedor_nome]

                            supabase.table("atas").update({
                                "nome": novo_nome,
                                "data_inicio": nova_data.isoformat(),
                                "data_validade": nova_validade_ata.isoformat(),
                                "fornecedor_id": novo_fornecedor_id,
                                "categoria_ata": nova_categoria_ata,
                                "link_ata": novo_link_ata,
                                "ata_renovavel": nova_info_renovacao_bool
                            }).eq("id", ata_id).execute()

                            st.success("Ata atualizada com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao atualizar a Ata: {e}")
            
                    # Buscar equipamentos vinculados à Ata
                    st.subheader("Equipamentos desta Ata")
                    st.write("Clique no equipamento que deseja atualizar informações")
                
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

                                    atualizar = st.form_submit_button("Editar Equipamento")

                                if atualizar:
                                    try:
                                        nova_espeficicacao_formatada = ' '.join(nova_especificacao.split()).upper()
                                        nova_marca_modelo_formatada = ' '.join(nova_marca_modelo.split()).upper()
                                        supabase.table("equipamentos").update({
                                            "especificacao": nova_espeficicacao_formatada,
                                            "marca_modelo": nova_marca_modelo_formatada,
                                            "quantidade": nova_qtd,
                                            "saldo_disponivel": novo_saldo,
                                            "valor_unitario": novo_valor_unit,
                                            "valor_total": valor_total
                                        }).eq("id", equipamento["id"]).execute()
                                        st.success(f"Equipamento '{nova_espeficicacao_formatada}' atualizado com sucesso!")
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar equipamento: {e}")

            elif aba == "Excluir":
                st.subheader("Excluir Ata/Equipamento(s) da Ata")
                try:
                    response_atas = supabase.table("atas").select("id, nome, data_inicio, data_validade, categoria_ata, fornecedores(nome), link_ata").order("nome").execute() 
                    atas_data = response_atas.data
                    atas_dict = {a["nome"]: a["id"] for a in atas_data}
                    atas_nomes = ["Selecione"] + list(atas_dict.keys())

                    ata_selecionada = st.selectbox("Selecione uma Ata para excluir", atas_nomes, key="selecionar_ata_exclusao")

                    if ata_selecionada != "Selecione":
                        ata_id = atas_dict[ata_selecionada]
                        ata_info = next((a for a in atas_data if a["id"] == ata_id), None)

                        if ata_info:
                            fornecedor_nome = ata_info.get("fornecedores", {}).get("nome", "Não informado")

                            ata_df = pd.DataFrame([{
                                "Número": ata_info["nome"],
                                "Data de início": ata_info["data_inicio"],
                                "Data de validade": ata_info["data_validade"],
                                "Fornecedor": fornecedor_nome,
                                "Categoria": categoria_ata,
                                "N° Protocolo SEI": ata_info["link_ata"]
                            }])
                            
                            st.dataframe(ata_df)

                            with st.form("botao_excluir_ata", border=False):
                                confirmar = st.checkbox("Confirmo que desejo excluir esta ata.")
                                excluir = st.form_submit_button("Excluir Ata")

                            if excluir and confirmar:
                                try:
                                    supabase.table("atas").delete().eq("id", ata_id).execute()
                                    st.success("Ata excluída com sucesso!")
                                except Exception as e:
                                    st.error(f"Erro ao excluir ata: {e}")
                            elif excluir and not confirmar:
                                st.warning("Você precisa confirmar antes de excluir.")

                            # Seção de exclusão de equipamentos
                            st.subheader("Equipamentos desta Ata")

                            try:
                                response_eq = supabase.table("equipamentos").select("id, especificacao, saldo_disponivel").eq("ata_id", ata_id).execute()
                                equipamentos_data = response_eq.data

                                if equipamentos_data:
                                    for eq in equipamentos_data:
                                        with st.expander(f"{eq['especificacao']} (Saldo: {eq['saldo_disponivel']})"):
                                            with st.form(f"form_excluir_eq_{eq['id']}", border=False):
                                                confirmar_eq = st.checkbox("Confirmo que desejo excluir este equipamento.", key=f"chk_{eq['id']}")
                                                excluir_eq = st.form_submit_button("Excluir Equipamento")
                                                
                                                if excluir_eq and confirmar_eq:
                                                    try:
                                                        supabase.table("equipamentos").delete().eq("id", eq["id"]).execute()
                                                        st.success(f"Equipamento '{eq['especificacao']}' excluído com sucesso!")
                                                    except Exception as e:
                                                        st.error(f"Erro ao excluir equipamento: {e}")
                                                elif excluir_eq and not confirmar_eq:
                                                    st.warning("Você precisa confirmar antes de excluir.")
                                else:
                                    st.info("Nenhum equipamento cadastrado nesta Ata.")

                            except Exception as e:
                                st.error(f"Erro ao carregar equipamentos: {e}")

                except Exception as e:
                    st.error(f"Erro ao carregar atas: {e}")

                            
    # Empenhos -----------------------------------------------------------------------------------------------------------------                
    with tabs[2]:
        col1, col2 = st.columns([1, 4])

        # Sessão de estado para armazenar aba ativa
        if "aba_empenhos" not in st.session_state:
            st.session_state.aba_empenhos = "Empenhar"

        with col1:
            st.image("assets/logos.svg", width=300)
            botoes_empenhos = ["Empenhar", "Consultar", "Atualizar", "Excluir"]
            for b in botoes_empenhos:
                if st.button(b, key=f"botao_{b}_empenhos"):
                    st.session_state.aba_empenhos = b
        
        with col2:
            aba = st.session_state.aba_empenhos

            if aba == "Empenhar":
                st.subheader("Empenhar")
                try:
                    response = supabase.table("atas").select("id, nome, data_validade").order("nome", desc=False).execute()
                    atas_result = response.data
                    atas_dict = {a["nome"]: {"id": a["id"], "data_validade":a["data_validade"]} for a in atas_result}
                    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar atas: {e}")
                    atas_cadastradas = ["Selecione"]
                    atas_dict = {}

                ata_nome = st.selectbox("Selecione a Ata", atas_cadastradas, key="selecione_ata_nome_empenho")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]["id"]
                    ata_validade = atas_dict[ata_nome]["data_validade"]

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

                                with st.form("form_registrar_empenho"):
                                    quantidade = st.number_input("Quantidade empenhada", min_value=1, max_value=saldo_disp, step=1)
                                    data_empenho = st.date_input("Data do Empenho", format="DD/MM/YYYY")
                                    observacao = st.text_input("Observação (opcional)")

                                    registrar_empenho = st.form_submit_button("Cadastrar Empenho")    
                                    if registrar_empenho:
                                        ata_validade_date = date.fromisoformat(ata_validade)
                                        if data_empenho > ata_validade_date:
                                            ata_validade_formatada = date.fromisoformat(ata_validade).strftime("%d/%m/%Y")
                                            st.error(f"A data do empenho é posterior à validade da Ata (vencida em {ata_validade_formatada}). Cadastro não permitido.")
                                        else:
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

                                                st.success("Empenho cadastrado com sucesso!")
                                            except Exception as e:
                                                st.error(f"Erro ao cadastrar empenho: {e}")
                        else:
                            st.warning("Nenhum equipamento com saldo disponível para esta Ata.")
                    except Exception as e:
                        st.error(f"Erro ao buscar equipamentos: {e}")
            
            if aba == "Consultar":
                st.subheader("Consultar Empenhos cadastrados")

                try:
                    response = supabase.table("atas").select("id, nome").order("nome", desc=False).execute()
                    atas_result = response.data
                    atas_dict = {a["nome"]: a["id"] for a in atas_result}
                    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar atas: {e}")
                    atas_cadastradas = ["Selecione"]
                    atas_dict = {}

                ata_nome = st.selectbox("Selecione a Ata para consultar empenhos", atas_cadastradas, key="selecione_ata_nome_empenho_consulta")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]["id"]
                    
                    try:
                        response = supabase.rpc("empenhos_por_ata", {"ata_id_param": ata_id}).execute()
                        empenhos = response.data

                        if empenhos: 
                            empenhos_df = pd.DataFrame(empenhos).drop(columns=['id'])
                            empenhos_df['data_empenho'] = pd.to_datetime(empenhos_df['data_empenho']).dt.strftime('%d/%m/%Y')

                            empenhos_df = empenhos_df.rename(columns={
                                'data_empenho': 'Data do Empenho',
                                'especificacao': 'Especificação',
                                'quantidade_empenhada': 'Quantidade Empenhada',
                                'observacao':'Observação'
                            })

                            st.dataframe(empenhos_df, height=300)

                        else:
                            st.info("Nenhum empenho cadastrado para esta Ata.")
                    except Exception as e:
                        st.error(f"Erro ao buscar empenhos: {e}")

            if aba == "Atualizar":
                st.subheader("Atualizar Empenhos cadastrados")

                try:
                    response = supabase.table("atas").select("id, nome, data_validade").order("nome", desc=False).execute()
                    atas_result = response.data
                    atas_dict = {a["nome"]: {"id": a["id"], "data_validade": a["data_validade"]} for a in atas_result}
                    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar atas: {e}")
                    atas_cadastradas = ["Selecione"]
                    atas_dict = {}

                ata_nome = st.selectbox("Selecione a Ata para atualizar empenhos", atas_cadastradas, key="selecione_ata_nome_empenho_atualizar")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]["id"]
                    ata_validade = atas_dict[ata_nome]["data_validade"]

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

                                        atualizar = st.form_submit_button("Atualizar Empenho")

                                    if atualizar:
                                        ata_validade_date = date.fromisoformat(ata_validade)
                                        if nova_data > ata_validade_date:
                                                ata_validade_formatada = date.fromisoformat(ata_validade).strftime("%d/%m/%Y")
                                                st.error(f"A data do empenho é posterior à validade da Ata (vencida em {ata_validade_formatada}). Cadastro não permitido.")
                                        else:
                                                try:
                                                    supabase.table("empenhos").update({
                                                        "quantidade_empenhada": nova_quantidade,
                                                        "data_empenho": nova_data.isoformat(),
                                                        "observacao": nova_obs
                                                    }).eq("id", emp["id"]).execute()
                                                    st.success("Empenho atualizado com sucesso.")
                                                except Exception as e:
                                                    st.error(f"Erro ao atualizar empenho: {e}")

                        else:
                            st.info("Nenhum empenho cadastrado para esta Ata.")
                    except Exception as e:
                        st.error(f"Erro ao buscar empenhos: {e}")
            
            if aba == "Excluir":
                st.subheader("Excluir empenhos")
                
                try:
                    response = supabase.table("atas").select("id, nome").order("nome", desc=False).execute()
                    atas_result = response.data
                    atas_dict = {a["nome"]: a["id"] for a in atas_result}
                    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

                except Exception as e:
                    st.error(f"Erro ao buscar atas: {e}")
                    atas_cadastradas = ["Selecione"]
                    atas_dict = {}

                ata_nome = st.selectbox("Selecione Ata para excluir empenho(s)", atas_cadastradas, key="selecione_ata_nome_empenho_excluir")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]
                    
                    try:
                        response = supabase.rpc("empenhos_por_ata", {"ata_id_param": ata_id}).execute()
                        empenhos = response.data

                        if empenhos: 
                            # Cria descrições amigáveis para cada empenho
                            opcoes_empenho = {
                                f"{e['quantidade_empenhada']}x {e['especificacao']} - {pd.to_datetime(e['data_empenho']).strftime('%d/%m/%Y')}": e['id']
                                for e in empenhos
                            }
                            opcoes_lista = ["Selecione"] + list(opcoes_empenho.keys())

                            empenho_escolhido = st.selectbox("Selecione o empenho que deseja excluir", opcoes_lista)

                            if empenho_escolhido != "Selecione":
                                empenho_id = opcoes_empenho[empenho_escolhido]

                                # Mostra os detalhes antes de excluir
                                empenho_info = next(e for e in empenhos if e['id'] == empenho_id)
                                info_df = pd.DataFrame([empenho_info]).rename(columns={
                                    'data_empenho': 'Data do Empenho',
                                    'especificacao': 'Especificação',
                                    'quantidade_empenhada': 'Quantidade Empenhada',
                                    'observacao': 'Observação'
                                }).drop(columns=['id'])
                                info_df['Data do Empenho'] = pd.to_datetime(info_df['Data do Empenho']).dt.strftime('%d/%m/%Y')
                                st.dataframe(info_df)

                                # Confirmação e exclusão
                                with st.form("botao_excluir_empenho", border=False):
                                    confirmar = st.checkbox("Confirmo que desejo excluir este empenho.")
                                    excluir = st.form_submit_button("Excluir Empenho")

                                if excluir and confirmar:
                                    try:
                                        supabase.table("empenhos").delete().eq("id", empenho_id).execute()
                                        st.success("Empenho excluído com sucesso.")
                                    except Exception as e:
                                        st.error(f"Erro ao excluir empenho: {e}")
                                elif excluir and not confirmar:
                                    st.warning("Você precisa confirmar antes de excluir.")



                        else:
                            st.info("Nenhum empenho cadastrado para esta Ata.")
                    except Exception as e:
                        st.error(f"Erro ao buscar empenhos: {e}")



    # Histórico de Empenhos -----------------------------------------------------------------------------------------------------------------
    with tabs[3]:

        col1, col2 = st.columns([1,4])

        with col1:
            st.image("assets/logos.svg", width=300)
        with col2:
            st.subheader("Histórico Geral de Empenhos")

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
                data_inicio = st.date_input("Data inicial", value=pd.to_datetime("2023-01-01"), format= 'DD/MM/YYYY', key="data_inicio_filtro")
            with col2:
                data_fim = st.date_input("Data final", value=pd.to_datetime("today"), format= 'DD/MM/YYYY', key="data_fim_filtro")

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
                st.dataframe(df_empenhos, height=200)

                st.subheader("📊 Análises e Gráficos")

                # Resumos
                total_empenhos = len(df_empenhos)
                quantidade_total_empenhada = df_empenhos["Quantidade"].sum()
                atas_envolvidas = df_empenhos["Ata"].nunique()
                
                bg_color = "#f0f2f6"
                text_color = "#333333"
                number_color = "#004aad"

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"""
                        <div class="metric-box" style="--bg-color:{bg_color}; --text-color:{text_color}; --number-color:{number_color};">
                            <h5>Total de Empenhos</h5>
                            <h2>{total_empenhos}</h2>
                        </div>
                    """, unsafe_allow_html=True)

                with col2:
                    st.markdown(f"""
                        <div class="metric-box" style="--bg-color:{bg_color}; --text-color:{text_color}; --number-color:{number_color};">
                            <h5>Quantidade Total Empenhada</h5>
                            <h2>{quantidade_total_empenhada}</h2>
                        </div>
                    """, unsafe_allow_html=True)

                with col3:
                    st.markdown(f"""
                        <div class="metric-box" style="--bg-color:{bg_color}; --text-color:{text_color}; --number-color:{number_color};">
                            <h5>Atas Envolvidas</h5>
                            <h2>{atas_envolvidas}</h2>
                        </div>
                    """, unsafe_allow_html=True)

                aba1, aba2, aba3 = st.tabs(["Por Ata", "Por Mês", "Por Equipamento"])

                with aba1:
                    total_por_ata = df_empenhos.groupby("Ata")["Quantidade"].sum().reset_index()
                    fig_ata = px.bar(total_por_ata, x="Ata", y="Quantidade", title="Total de Empenhos por Ata")
                    fig_ata.update_yaxes(dtick=5)
                    st.plotly_chart(fig_ata, use_container_width=True)

                with aba2:
                    # Garante que é datetime pra gerar o AnoMes
                    df_empenhos["Data do Empenho"] = pd.to_datetime(df_empenhos["Data do Empenho"])

                    # Cria coluna formatada tipo 'Abr/2025'
                    df_empenhos["AnoMes"] = df_empenhos["Data do Empenho"].dt.strftime('%b/%Y')

                    # Agrupa por essa nova coluna
                    quantidade_mensal = df_empenhos.groupby("AnoMes")["Quantidade"].sum().reset_index()

                    # Cria gráfico com eixo categórico
                    fig_mensal = px.line(
                        quantidade_mensal,
                        x="AnoMes",
                        y="Quantidade",
                        markers=True,
                        title="Quantidade Empenhada por Mês"
                    )

                    fig_mensal.update_xaxes(type="category", title_text="Ano/Mês")
                    fig_mensal.update_yaxes(dtick=5)

                    st.plotly_chart(fig_mensal, use_container_width=True)

                with aba3:
                    top_eq = df_empenhos.groupby("Equipamento")["Quantidade"].sum().nlargest(5).reset_index()

                    # Quebrar nomes longos em várias linhas, respeitando palavras
                    top_eq["Equipamento"] = top_eq["Equipamento"].apply(lambda x: '<br>'.join(textwrap.wrap(x, width=20)))

                    fig_top_eq = px.bar(top_eq, x="Quantidade", y="Equipamento", orientation="h",
                                        title="Top 5 Equipamentos Mais Empenhados")
                    fig_top_eq.update_xaxes(dtick=5)
                    fig_top_eq.update_yaxes(title_text="")
                    st.plotly_chart(fig_top_eq, use_container_width=True)

            else:
                st.info("Nenhum empenho encontrado com os filtros selecionados.")
        except Exception as e:
            st.error(f"Erro ao buscar empenhos: {e}")


    # Relatórios de Consumo e Status -----------------------------------------------------------------------------------------------------------------
    with tabs[4]:
        col1, col2 = st.columns([1,4])

        with col1:
            st.image("assets/logos.svg", width=300)
        with col2:
            st.subheader("Relatórios de Consumo e Status")

        try:
            # Buscar atas
            atas_response = supabase.table("atas").select("id, nome, data_validade").execute()
            atas_data = {ata["id"]: ata for ata in atas_response.data}

            # Buscar equipamentos
            equipamentos_response = supabase.table("equipamentos").select("especificacao, quantidade, saldo_disponivel, ata_id, valor_unitario").order("ata_id").execute()
            equipamentos_data = equipamentos_response.data

            if equipamentos_data:
                relatorio_consumo = []
                for eq in equipamentos_data:
                    ata = atas_data.get(eq["ata_id"])

                    if not ata:
                        continue

                    saldo_utilizado = eq["quantidade"] - eq["saldo_disponivel"]
                    valor_total = eq["quantidade"] * eq["valor_unitario"]
                    valor_utilizado = saldo_utilizado * eq["valor_unitario"]
                    percentual_utilizado = (saldo_utilizado / eq["quantidade"]) * 100 if eq["quantidade"] else 0
                    percentual_disponivel = 100 - percentual_utilizado

                    relatorio_consumo.append({
                        "Ata": ata["nome"],
                        "Equipamento": eq["especificacao"],
                        "Qtd Total": eq["quantidade"],
                        "Saldo Utilizado": saldo_utilizado,
                        "Saldo Disponível": eq["saldo_disponivel"],
                        "% Utilizado": f"{percentual_utilizado:.1f}%",
                        "% Disponível": f"{percentual_disponivel:.1f}%",
                        "Valor Total (R$)": valor_total,
                        "Valor Utilizado (R$)": valor_utilizado,
                        "Data de Validade": ata["data_validade"]
                    })

                # Criar DataFrame
                relatorio_df = pd.DataFrame(relatorio_consumo)

                # Manter validade como datetime antes de formatar
                relatorio_df["Data de Validade"] = pd.to_datetime(relatorio_df["Data de Validade"])

                # Remover atas vencidas há mais de 30 dias
                hoje = pd.Timestamp.today()
                relatorio_df = relatorio_df[(relatorio_df["Data de Validade"] >= hoje - pd.Timedelta(days=30))]

                # Garantir que % utilizado é float antes de formatar
                relatorio_df["% Utilizado"] = (
                    relatorio_df["% Utilizado"]
                    .astype(str)
                    .str.replace('%', '', regex=False)
                    .str.replace(',', '.', regex=False)
                    .astype(float)
                )

                # Formatações
                relatorio_df["Data de Validade"] = relatorio_df["Data de Validade"].dt.strftime('%d/%m/%Y')
                relatorio_df["Valor Total (R$)"] = relatorio_df["Valor Total (R$)"].apply(formatar_moeda)
                relatorio_df["Valor Utilizado (R$)"] = relatorio_df["Valor Utilizado (R$)"].apply(formatar_moeda)
                relatorio_df["% Utilizado"] = relatorio_df["% Utilizado"].map(lambda x: f"{x:.1f}%")


                st.dataframe(relatorio_df, height=200)

            else:
                st.info("Nenhum consumo cadastrado ainda.")

            hoje = datetime.today().date()
            data_limite = hoje + timedelta(days=30)

            # Criar dicionário: ata_id -> saldo total disponível
            saldo_por_ata = {}
            for eq in equipamentos_data:
                ata_id = eq["ata_id"]
                saldo_por_ata[ata_id] = saldo_por_ata.get(ata_id, 0) + eq["saldo_disponivel"]

            atas_vencidas = [
                ata for ata in atas_data.values()
                if ata["data_validade"] and pd.to_datetime(ata["data_validade"]).date() < hoje
            ]

            atas_vencendo = [
                ata for ata in atas_data.values()
                if ata["data_validade"] and hoje < pd.to_datetime(ata["data_validade"]).date() <= data_limite
            ]

            with st.container(border=True):
                st.warning("🔔 Atas vencendo nos próximos 30 dias:")
                if atas_vencendo:
                    for ata in sorted(atas_vencendo, key=lambda x: x["data_validade"]):
                        validade = pd.to_datetime(ata["data_validade"]).strftime('%d/%m/%Y')
                        saldo = saldo_por_ata.get(ata["id"], 0)
                        st.write(f"**Ata:** {ata['nome']} — **Validade:** {validade}")
                        st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• **Saldo restante:** {saldo}")
                else:
                    st.write("Não há atas vencendo nos próximos 30 dias.")

        
            with st.container(border=True):
                st.markdown("""
                        <div style='background-color:#f8d7da; padding:17px; border-radius:7px; position:relative; margin-bottom:1em'>
                            ❌    Atas vencidas:
                            <span style='float:right; cursor:help;' title='Atas com renovação vencida há mais de 30 dias não são mostradas.'>ℹ️</span>
                        </div>
                        """, unsafe_allow_html=True)
                if atas_vencidas:
                    for ata in sorted(atas_vencidas, key=lambda x: x["data_validade"]):
                        validade_dt = pd.to_datetime(ata["data_validade"])
                        dias_vencida = (pd.Timestamp.today() - validade_dt).days

                        if 0 < dias_vencida <= 30:
                            validade = validade_dt.strftime('%d/%m/%Y')
                            saldo = saldo_por_ata.get(ata["id"], 0)
                            st.write(f"**Ata:** {ata['nome']} — **Vencida em:** {validade}")
                            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• **Saldo restante:** {saldo}")
                else:
                    st.write("Não há atas vencidas nos últimos 30 dias.")

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")

    # Renovação da Ata -----------------------------------------------------------------------------------------------------------------------------
    if 'prazo_renovacao_ata' not in st.session_state:
        st.session_state.prazo_renovacao_ata = get_config('prazo_renovacao_ata')

    with tabs[5]:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image("assets/logos.svg", width=300)
        with col2:
            st.subheader("Renovação de atas")

        # Espaço reservado para o texto
        prazo_placeholder = st.empty()
        prazo_placeholder.markdown(f"**Prazo padrão de renovação:** {st.session_state.prazo_renovacao_ata} meses")

        with st.expander("Alterar prazo de renovação"):
            with st.form("form_alterar_prazo"):
                novo_prazo = st.number_input("Novo prazo de renovação (meses)", min_value=1,max_value=96, value=st.session_state.prazo_renovacao_ata)
                submitted = st.form_submit_button("Salvar novo prazo")
                if submitted:
                    update_config('prazo_renovacao_ata', novo_prazo)
                    st.session_state.prazo_renovacao_ata = novo_prazo
                    st.success(f"Prazo atualizado para {novo_prazo} meses!")
                    st.rerun() 

        st.markdown("---")

        try:
            # Buscar atas
            atas_response = supabase.table("atas").select("id, nome, data_inicio").execute()
            atas_data = {ata["id"]: ata for ata in atas_response.data}

            if atas_data:
                relatorio_renovacao = []
                hoje = date.today()
                prazo_meses = st.session_state.prazo_renovacao_ata

                # Definir listas para armazenar atas com alertas
                renovacoes_90_dias = []
                renovacoes_30_dias = []
                renovacoes_vencidas = []

                for ata in atas_data.values():
                    if not ata:
                        continue

                    # Garantindo que data_inicio está no formato date
                    data_inicio = date.fromisoformat(ata["data_inicio"])

                    # Calculando a data de renovação
                    data_renovacao = data_inicio + relativedelta(months=prazo_meses)
                    dias_para_renovacao = (data_renovacao - hoje).days

                    relatorio_renovacao.append({
                        "Ata": ata["nome"],
                        "Data Início": data_inicio.strftime('%d/%m/%Y'),
                        "Data Renovação": data_renovacao.strftime('%d/%m/%Y'),
                        "Dias para renovação": dias_para_renovacao
                    })

                    # Adicionar à lista de renovações próximas (90 e 30 dias)
                    if dias_para_renovacao < 0:
                        if dias_para_renovacao > -31:
                            renovacoes_vencidas.append(f"**Ata:** {ata['nome']} — Vencida há {-dias_para_renovacao} dia(s)")
                    elif dias_para_renovacao <= 30:
                        renovacoes_30_dias.append(f"**Ata:** {ata['nome']} — {dias_para_renovacao} dias restantes")
                    elif 30 < dias_para_renovacao <= 90:
                        renovacoes_90_dias.append(f"**Ata:** {ata['nome']} — {dias_para_renovacao} dias restantes")
            

                relatorio_df = pd.DataFrame(relatorio_renovacao)
                st.dataframe(relatorio_df, height=150)

                # Exibir alertas de renovação
                with st.container(border=True):
                    st.warning("🔔 Renovações nos próximos 90 dias:")
                    if renovacoes_90_dias:
                        for alerta in renovacoes_90_dias:
                            st.write(alerta)
                    else:
                        st.write("Não há atas com renovações nos próximos 90 dias.")

                with st.container(border=True):
                    st.warning("⚠️ Renovações nos próximos 30 dias:")
                    if renovacoes_30_dias:
                        for alerta in renovacoes_30_dias:
                            st.write(alerta)
                    else:
                        st.write("Não há atas com renovações nos próximos 30 dias.")

                with st.container(border=True):
                    st.markdown("""
                        <div style='background-color:#f8d7da; padding:17px; border-radius:7px; position:relative; margin-bottom:1em'>
                            ❌    Atas com renovação vencida:
                            <span style='float:right; cursor:help;' title='Atas com renovação vencida há mais de 30 dias não são mostradas.'>ℹ️</span>
                        </div>
                        """, unsafe_allow_html=True)
                    if renovacoes_vencidas:
                        for alerta in renovacoes_vencidas:
                                st.write(alerta)
                    else:
                        st.write("Não há atas com renovações vencidas nos últimos 30 dias.")
                    
            else:
                st.info("Nenhuma ata cadastrada ainda.")

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
