import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
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
            <p style='margin-top:0;'>Bem-vindo(a), {usuario.get('nome', 'usuário')}</p>""",
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
    
    def buscar_equipamentos(colunas=None):
        colunas_str = ", ".join(colunas) if colunas else "*"
        return supabase.table("equipamentos").select(colunas_str).order("especificacao").execute().data

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
                st.success(f"Item '{espeficicacao_formatada}' cadastrado com sucesso na ata '{ata_nome}'!")
            except Exception as e:
                st.error(f"Erro ao cadastrar item: {e}")
        else:
            st.warning("Preencha todos os campos obrigatórios.")

    def selecionar_categoria():
        categorias_selecionadas = st.multiselect("Escolha a(s) categoria(s)", ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"], placeholder="Selecione", key="selecionar_categoria_funcao")
                
        try:
            atas_result = buscar_atas()

            if categorias_selecionadas:
                atas_filtradas = [ata for ata in atas_result if ata["categoria_ata"] in categorias_selecionadas]
            else:
                atas_filtradas = atas_result

            atas_dict = {a["nome"]: a["id"] for a in atas_filtradas}
            atas_opcoes = ["Selecione"] + list(atas_dict.keys())

        except Exception as e:
            st.error(f"Erro ao buscar atas: {e}")
            atas_opcoes = ["Selecione"]
            atas_dict = {}
        
        return [atas_opcoes, atas_dict]
            
    def selecionar_categoria_para_empenho():
        categorias_selecionadas = st.multiselect("Escolha a(s) categoria(s)", ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"], placeholder="Selecione", key="selecionar_categoria_empenho_funcao")

        try:       
            atas_result = buscar_atas()

            if categorias_selecionadas:
                atas_filtradas = [ata for ata in atas_result if ata["categoria_ata"] in categorias_selecionadas]
            else:
                atas_filtradas = atas_result

            atas_dict = {a["nome"]: {"id": a["id"], "data_validade":a["data_validade"]} for a in atas_filtradas}
            atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

        except Exception as e:
            st.error(f"Erro ao buscar atas: {e}")
            atas_cadastradas = ["Selecione"]
            atas_dict = {}
        
        return [atas_cadastradas, atas_dict]

    # Estabelecendo o layout com abas
    tabs = st.tabs(["Relatórios de Consumo e Status", "Fornecedores", "Atas", "Empenhos", "Histórico Geral de Empenhos", "Renovação de Atas"])
    
    # Relatórios de Consumo e Status -----------------------------------------------------------------------------------------------------------------
    with tabs[0]:
        col1, col2 = st.columns([1,4])

        with col1:
            st.image("assets/logos.svg", width=300)
        with col2:
            st.subheader("Relatórios de Consumo e Status")

        try:
            # Buscar atas
            atas_response = buscar_atas(["id", "nome", "data_validade", "categoria_ata"])
            atas_data = {ata["id"]: ata for ata in atas_response}

            # Buscar equipamentos
            equipamentos_data = buscar_equipamentos(["especificacao", "quantidade", "saldo_disponivel", "ata_id", "valor_unitario"])

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
                        "Ata ID": ata["id"],
                        "Categoria": ata["categoria_ata"],
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

                categorias_selecionadas = st.multiselect("Escolha a(s) categoria(s)", ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"], placeholder="Selecione", key="selecionar_categoria_relatorio")
                
                if categorias_selecionadas:
                    relatorio_df_filtrado = relatorio_df[relatorio_df["Categoria"].isin(categorias_selecionadas)]
                    ata_ids_filtradas = set(relatorio_df_filtrado["Ata ID"].unique())

                    st.dataframe(relatorio_df_filtrado, height=200)

                    hoje = datetime.today().date()
                    data_limite = hoje + timedelta(days=30)

                    # Criar dicionário: ata_id -> saldo total disponível
                    saldo_por_ata = {}
                    for eq in equipamentos_data:
                        ata_id = eq["ata_id"]
                        saldo_por_ata[ata_id] = saldo_por_ata.get(ata_id, 0) + eq["saldo_disponivel"]

                    atas_vencidas = [
                        ata for ata in atas_data.values()
                        if ata["id"] in ata_ids_filtradas and ata["data_validade"] and pd.to_datetime(ata["data_validade"]).date() < hoje
                    ]

                    atas_vencendo = [
                        ata for ata in atas_data.values()
                        if ata["id"] in ata_ids_filtradas and ata["data_validade"] and hoje < pd.to_datetime(ata["data_validade"]).date() <= data_limite
                    ]

                    with st.container(border=True):
                        st.markdown("""
                            <div style='background-color:#f7f090; padding:17px; border-radius:7px; position:relative; margin-bottom:1em'>
                                ⚠️ Atas vencendo nos próximos 30 dias:
                            </div>
                            """, unsafe_allow_html=True)
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

            else:
                st.info("Nenhum consumo cadastrado ainda.")


        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")


    # Fornecedores -----------------------------------------------------------------------------------------------------------------
    with tabs[1]:
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
                with st.form("novo_fornecedor", border=False):
                    nome_fornecedor = st.text_input("Nome do Fornecedor")

                    col1, col2 = st.columns([1,2])
                    with col1:
                        cnpj = st.text_input("CNPJ (formato: 00.000.000/0000-00)")
                    with col2:
                        email = st.text_input("E-mail")
                    
                    endereco = st.text_input("Endereço")
                    col1, col2 = st.columns([2,1])
                    with col1:
                        telefone = st.text_input("Telefone")
                    with col2:
                        cep = st.text_input("CEP (formato = 00000-000)", max_chars=9)
                    
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
                        df_fornecedores = df_fornecedores.drop(columns=["id"]).rename(columns={
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
                                with st.form("form_editar_fornecedor", border=False):
                                    novo_nome = st.text_input("Nome do Fornecedor", value=fornecedor_info["nome"])

                                    col1, col2 = st.columns([1,2])
                                    with col1:
                                        novo_cnpj = st.text_input("CNPJ (formato: 00.000.000/0000-00)", value=fornecedor_info["cnpj"])
                                    with col2:
                                        novo_email = st.text_input("E-mail", value=fornecedor_info["email"])
                                    
                                    novo_endereco = st.text_input("Endereço", value=fornecedor_info["endereco"])
                                    col1, col2 = st.columns([2,1])
                                    with col1:
                                        novo_telefone = st.text_input("Telefone", value=fornecedor_info["telefone"])
                                    with col2:
                                        novo_cep = st.text_input("CEP (formato = 00000-000)", max_chars=9, value=fornecedor_info["cep"])

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
    with tabs[2]:
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
                with st.form("nova_ata", border=False):
                    col1, col2, col3 = st.columns([1,1,1])
                    with col1:
                        num_ata = st.text_input("Número da Ata (ex: 12/2024, 1234/2025)")
                    with col2:
                        categoria_ata = st.selectbox("Categoria", ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"], key="selecione_categoria_ata")
                    with col3:
                        ata_renovavel = st.radio("Ata renovável?", options=["Sim", "Não"], horizontal=True)
                        renovavel_bool = ata_renovavel == "Sim"

                    fornecedor_exibido = st.selectbox("Fornecedor", fornecedores_cadastrados, key="selecione_fornecedor_nome", help="Digite o nome ou CNPJ para localizar o fornecedor.")
                    
                    col1, col2, col3 = st.columns([1,1,1])
                    with col1:
                        data_ata = st.date_input("Data da Ata", format="DD/MM/YYYY")
                    with col2:
                        validade_ata = st.date_input("Validade da Ata", min_value=data_ata, format="DD/MM/YYYY")
                    with col3:
                        link_ata = st.text_input("Número do Protocolo SEI")
                    

                    submit_ata = st.form_submit_button("Cadastrar Ata")

                    if submit_ata:
                        cadastrar_ata(num_ata, data_ata, validade_ata, fornecedor_exibido, link_ata, categoria_ata, ata_renovavel, renovavel_bool)

                # Adicionar Equipamento na Ata --------------------------------------------
                st.subheader("Adicionar Item a uma Ata")

                atas_opcoes, atas_dict = selecionar_categoria()
                atas_result = buscar_atas(["id", "nome"])

                ata_nome = st.selectbox("Selecione a Ata", atas_opcoes, key="selecione_ata_nome")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]

                    with st.form("novo_equipamento", border=False):
                        col1, col2 = st.columns([1,1])
                        with col1:
                            especificacao = st.text_input("Especificação")
                        with col2:
                            marca_modelo = st.text_input("Marca/Modelo")
                        
                        col1, col2, col3 = st.columns([1,1,1])
                        with col1:
                            quantidade = st.number_input("Quantidade", min_value=1, step=1)
                        with col2:
                            saldo_disponivel = st.number_input("Saldo disponível", min_value=0, step=1)
                        with col3:
                            valor_unitario = st.number_input("Valor Unitário (R$)", min_value=0.0, format="%.2f")
                        valor_total = valor_unitario * quantidade

                        submit_equipamento = st.form_submit_button("Adicionar Item")

                        if submit_equipamento:
                            cadastrar_equipamento(especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario)
                        

            elif aba == "Consultar":
                st.subheader("Consultar Atas Cadastradas")

                atas_opcoes, atas_dict = selecionar_categoria()
                atas_result = buscar_atas()
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
                        fornecedor_nome = buscar_fornecedor_por_id(ata_info["fornecedor_id"])["nome"] 
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

                            st.subheader("Itens dessa Ata")

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
                                st.info("Nenhum item cadastrado para esta Ata.")
                        except Exception as e:
                            st.error(f"Erro ao buscar itens: {e}")

            elif aba == "Atualizar":
                st.subheader("Atualizar dados de uma Ata")

                atas_opcoes, atas_dict = selecionar_categoria()
                atas_result = buscar_atas()
                ata_selecionada = st.selectbox("Selecione uma Ata para atualizar dados", atas_opcoes)

                if ata_selecionada != "Selecione":
                    ata_id = atas_dict[ata_selecionada]

                    # Buscar os dados da Ata selecionada
                    ata_info = next((a for a in atas_result if a["id"] == ata_id), None)
                    fornecedores_nomes = buscar_fornecedores(["nome"]) # lista de dicionarios {'nome': 'tal'}
                    nome_fornecedor_atual = buscar_fornecedor_por_id(ata_info["fornecedor_id"])["nome"]
                    categorias = ["Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"]
                    categoria_atual = ata_info["categoria_ata"]


                    with st.form("form_editar_ata", border=False):

                        col1, col2, col3 = st.columns([1,1,1])
                        with col1:
                            novo_nome = st.text_input("Nome da Ata", value=ata_info["nome"])
                        with col2:
                            nova_categoria_ata = st.selectbox("Categoria", categorias, key="selecione_nova_categoria_ata", index=categorias.index(categoria_atual) if categoria_atual else 0)
                        with col3:
                            nova_info_renovacao = st.radio("Ata renovável?", options=["Sim", "Não"], horizontal=True)
                            nova_info_renovacao_bool = nova_info_renovacao == 'Sim'

                        novo_fornecedor_nome = st.selectbox("Fornecedor", [dicionario["nome"] for dicionario in fornecedores_nomes], key="selecione_novo_fornecedor_nome", index=[dicionario["nome"] for dicionario in fornecedores_nomes].index(nome_fornecedor_atual) if nome_fornecedor_atual else 0)
                        
                        col1, col2, col3 = st.columns([1,1,1])
                        with col1:
                            nova_data = st.date_input("Data da Ata", format="DD/MM/YYYY", value=pd.to_datetime(ata_info["data_inicio"]).date())
                        with col2:
                            nova_validade_ata = st.date_input("Validade da Ata", min_value=nova_data, format="DD/MM/YYYY", value=pd.to_datetime(ata_info["data_validade"]).date())
                        with col3:
                            novo_link_ata = st.text_input("Número do Protocolo SEI")


                        atualizar = st.form_submit_button("Atualizar Ata")

                    if atualizar:
                        try:
                            fornecedores_data = listar_nomes_ids_fornecedores()
                            fornecedores_dict = {f["nome"]: f["id"] for f in fornecedores_data}
                            
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
                    st.subheader("Itens dessa Ata")
                    st.write("Clique no item que deseja atualizar informações")
                
                    response_equip = supabase.table("equipamentos").select("*").eq("ata_id", ata_id).execute()
                    equipamentos = response_equip.data

                    if not equipamentos:
                        st.info("Nenhum item cadastrado para essa Ata.")
                    else:
                        for equipamento in equipamentos:
                            with st.expander(f"Item: {equipamento['especificacao']}"):
                                with st.form(f"form_equip_{equipamento['id']}, border=False"):

                                    col1, col2 = st.columns([1,1])
                                    with col1:
                                        nova_especificacao = st.text_input("Especificação", value=equipamento["especificacao"])
                                    with col2:
                                        nova_marca_modelo = st.text_input("Marca/Modelo", value=equipamento["marca_modelo"])
                                    
                                    col1, col2, col3 = st.columns([1,1,1])
                                    with col1:
                                        nova_qtd = st.number_input("Quantidade", value=equipamento["quantidade"], step=1)
                                    with col2:
                                        novo_saldo = st.number_input("Saldo Disponível", value=equipamento["saldo_disponivel"], step=1)
                                    with col3:
                                        novo_valor_unit = st.number_input("Valor Unitário (R$)", value=float(equipamento["valor_unitario"]), step=0.01, format="%.2f")       
 
                                    # Valor total calculado automaticamente
                                    novo_valor_total = nova_qtd * novo_valor_unit
                                    st.text(f"Valor Total: R$ {valor_total:.2f}")

                                    atualizar = st.form_submit_button("Editar Item")

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
                                            "valor_total": novo_valor_total
                                        }).eq("id", equipamento["id"]).execute()
                                        st.success(f"Item '{nova_espeficicacao_formatada}' atualizado com sucesso!")
                                    except Exception as e:
                                        st.error(f"Erro ao atualizar item: {e}")

            elif aba == "Excluir":
                st.subheader("Excluir Ata/Itens da Ata")

                atas_opcoes, atas_dict = selecionar_categoria()
                atas_result = buscar_atas()
                ata_selecionada = st.selectbox("Selecione uma Ata para excluir", atas_opcoes, key="selecionar_ata_exclusao")

                if ata_selecionada != "Selecione":
                    ata_id = atas_dict[ata_selecionada]
                    ata_info = next((a for a in atas_result if a["id"] == ata_id), None)

                    if ata_info:
                        fornecedor_nome = ata_info.get("fornecedores", {}).get("nome", "Não informado")

                        ata_df = pd.DataFrame([{
                            "Número": ata_info["nome"],
                            "Data de início": ata_info["data_inicio"],
                            "Data de validade": ata_info["data_validade"],
                            "Fornecedor": fornecedor_nome,
                            "Categoria": ata_info["categoria_ata"],
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
                        st.subheader("Itens desta Ata")

                        try:
                            response_eq = supabase.table("equipamentos").select("id, especificacao, saldo_disponivel").eq("ata_id", ata_id).execute()
                            equipamentos_data = response_eq.data

                            if equipamentos_data:
                                for eq in equipamentos_data:
                                    with st.expander(f"{eq['especificacao']} (Saldo: {eq['saldo_disponivel']})"):
                                        with st.form(f"form_excluir_eq_{eq['id']}", border=False):
                                            confirmar_eq = st.checkbox("Confirmo que desejo excluir este item.", key=f"chk_{eq['id']}")
                                            excluir_eq = st.form_submit_button("Excluir item")
                                            
                                            if excluir_eq and confirmar_eq:
                                                try:
                                                    supabase.table("equipamentos").delete().eq("id", eq["id"]).execute()
                                                    st.success(f"Item '{eq['especificacao']}' excluído com sucesso!")
                                                except Exception as e:
                                                    st.error(f"Erro ao excluir item: {e}")
                                            elif excluir_eq and not confirmar_eq:
                                                st.warning("Você precisa confirmar antes de excluir.")
                            else:
                                st.info("Nenhum item cadastrado nesta Ata.")

                        except Exception as e:
                            st.error(f"Erro ao carregar itens: {e}")


                            
    # Empenhos -----------------------------------------------------------------------------------------------------------------                
    with tabs[3]:
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
                
                atas_cadastradas, atas_dict = selecionar_categoria_para_empenho()
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

                                with st.form("form_registrar_empenho", border=False):
                                    quantidade = st.number_input("Quantidade empenhada", min_value=1, max_value=saldo_disp, step=1)
                                    data_empenho = st.date_input("Data do Empenho", format="DD/MM/YYYY")
                                    observacao = st.text_input("Observação (opcional)")

                                    registrar_empenho = st.form_submit_button("Empenhar")    
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

                                                st.success("Empenho realizado com sucesso!")
                                            except Exception as e:
                                                st.error(f"Erro ao cempenhar: {e}")
                        else:
                            st.warning("Nenhum item com saldo disponível para esta Ata.")
                    except Exception as e:
                        st.error(f"Erro ao buscar equipamentos: {e}")
            
            if aba == "Consultar":
                st.subheader("Consultar empenhos realizados")

                atas_cadastradas, atas_dict = selecionar_categoria_para_empenho()
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
                st.subheader("Atualizar empenhos realizados")
                
                atas_cadastradas, atas_dict = selecionar_categoria_para_empenho()
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
                                    with st.form(f"form_emp_{emp['id']}", border=False):
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
                
                atas_cadastradas, atas_dict = selecionar_categoria_para_empenho()
                ata_nome = st.selectbox("Selecione Ata para excluir empenho(s)", atas_cadastradas, key="selecione_ata_nome_empenho_excluir")

                if ata_nome != "Selecione":
                    ata_id = atas_dict[ata_nome]["id"]
                    
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
    with tabs[4]:

        col1, col2 = st.columns([1,4])

        with col1:
            st.image("assets/logos.svg", width=300)
        with col2:
            st.subheader("Histórico Geral de Empenhos")

        try:
            # Filtrar por categoria
            categorias = ["Todos", "Equipamentos médicos", "Infraestrutura hospitalar", "Suprimentos"]
            categoria_filtro = st.multiselect("Filtrar por Categoria", categorias, key="selecione_categoria_filtro", placeholder="Selecione")

            # Buscar atas
            atas_data = buscar_atas(["id", "nome", "categoria_ata"])

            # Filtrar atas pelas categorias selecionadas
            if not categoria_filtro or "Todos" in categoria_filtro:
                atas_filtradas = atas_data
            else:
                atas_filtradas = [ata for ata in atas_data if ata["categoria_ata"] in categoria_filtro]   

            # Construir opções de atas
            atas_dict = {ata["nome"]: ata["id"] for ata in atas_filtradas}
            atas_opcoes = ["Todas"] + list(atas_dict.keys())

            # Filtrar por ata
            ata_filtro = st.multiselect("Filtrar por Ata", atas_opcoes, key="selecione_ata_filtro", placeholder="Selecione", )

            # Filtrar por Item
            equipamentos_data = buscar_equipamentos(["id", "especificacao", "ata_id"])

            if not ata_filtro or "Todas" in ata_filtro:
                # Quando a categoria está filtrada mas a ata não, buscar todos os equipamentos das atas dessa categoria
                if categoria_filtro:
                    ata_ids_filtradas = [ata["id"] for ata in atas_filtradas]
                    equipamentos_filtrados = [eq for eq in equipamentos_data if eq["ata_id"] in ata_ids_filtradas]
                else:
                    equipamentos_filtrados = equipamentos_data
            else:
                ata_id_selecionada = [atas_dict[nome_ata] for nome_ata in ata_filtro if nome_ata != "Todas"]
                equipamentos_filtrados = [equip for equip in equipamentos_data if equip["ata_id"] in ata_id_selecionada] 

            equipamentos_dict = {eq["id"]: eq for eq in equipamentos_filtrados}
            equipamentos_opcoes = ["Todos"] + sorted(list(set(eq["especificacao"] for eq in equipamentos_filtrados)))
            equipamento_filtro = st.multiselect("Filtrar por Item", equipamentos_opcoes, key="filtro_equipamento", placeholder="Selecione")

            # Considera todos se estiver vazio ou se "Todos" estiver selecionado
            if not equipamento_filtro or "Todos" in equipamento_filtro:
                equipamentos_selecionados = equipamentos_filtrados
            else:
                equipamentos_selecionados = [eq for eq in equipamentos_filtrados if eq["especificacao"] in equipamento_filtro]

            # Filtro de data
            col1, col2 = st.columns(2)
            with col1:
                data_inicio = st.date_input("Data inicial", value=pd.to_datetime("2024-01-01"), format= 'DD/MM/YYYY', key="data_inicio_filtro")
            with col2:
                data_fim = st.date_input("Data final", value=pd.to_datetime("today"), format= 'DD/MM/YYYY', key="data_fim_filtro")

            # Buscar empenhos
            st.subheader("Empenhos realizados")
            empenhos_response = supabase.table("empenhos").select("*").order("data_empenho", desc=True).execute()
            empenhos_data = empenhos_response.data

            empenhos_filtrados = []
            for emp in empenhos_data:
                equipamento = equipamentos_dict.get(emp["equipamento_id"])
                if not equipamento:
                    continue

                ata_id = equipamento["ata_id"]
                ata = next((a for a in atas_data if a["id"] == ata_id), None)
                if not ata:
                    continue

                especificacao = equipamento["especificacao"]
                data_empenho = pd.to_datetime(emp["data_empenho"])
                categoria = ata["categoria_ata"]
                ata_nome = ata["nome"]

                # Filtros por categoria (multiselect)
                if categoria_filtro and "Todas" not in categoria_filtro and categoria not in categoria_filtro:
                    continue

                # Filtros por ata (multiselect)
                if ata_filtro and "Todas" not in ata_filtro and ata_nome not in ata_filtro:
                    continue

                # Filtros por equipamento (multiselect)
                if equipamento_filtro and "Todos" not in equipamento_filtro and especificacao not in equipamento_filtro:
                    continue

                # Filtro de data
                if not (data_inicio <= data_empenho.date() <= data_fim):
                    continue

                empenhos_filtrados.append({
                    "Ata": ata_nome,
                    "Categoria": categoria,
                    "Equipamento": especificacao,
                    "Quantidade": emp["quantidade_empenhada"],
                    "Data do Empenho": data_empenho.strftime('%d/%m/%Y'),
                    "Observação": emp["observacao"]
                })


            if empenhos_filtrados:
                df_empenhos = pd.DataFrame(empenhos_filtrados)
                st.dataframe(df_empenhos, height=200)

                especificacoes_empenhadas = set(df_empenhos["Equipamento"])
                especificacoes_filtradas = set(eq["especificacao"] for eq in equipamentos_selecionados)

                especificacoes_nao_empenhadas = especificacoes_filtradas - especificacoes_empenhadas

                if especificacoes_nao_empenhadas:
                    st.markdown("**Itens desta(s) Ata(s) ainda não empenhados:**")
                    for especificacao in sorted(especificacoes_nao_empenhadas):
                        st.write(f"- {especificacao}")

                st.markdown("---")
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

                aba0, aba1, aba2, aba3 = st.tabs(["Por Categoria", "Por Ata", "Por Mês", "Por Item"])

                with aba0:
                    total_por_categoria = df_empenhos.groupby("Categoria")["Quantidade"].sum().reset_index()
                    fig_categoria = px.pie(total_por_categoria, names="Categoria", values="Quantidade", title="Empenhos por categoria")
                    #fig_categoria.update_traces(textinfo='percent+label')
                    st.plotly_chart(fig_categoria, use_container_width=True)

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
                                        title="Top 5 Itens Mais Empenhados")
                    fig_top_eq.update_xaxes(dtick=5)
                    fig_top_eq.update_yaxes(title_text="")
                    st.plotly_chart(fig_top_eq, use_container_width=True)

            else:
                st.info("Nenhum empenho encontrado com os filtros selecionados.")
        except Exception as e:
            st.error(f"Erro ao buscar empenhos: {e}")


    # Renovação da Ata -----------------------------------------------------------------------------------------------------------------------------
    resposta = supabase.table('configuracoes').select("valor").eq("chave", "prazo_renovacao_ata").single().execute()

    # Extrair e converter o valor para inteiro (meses)
    valor_str = resposta.data["valor"]
    try:
        prazo_renovacao_ata = int(valor_str)
    except ValueError:
        prazo_renovacao_ata = 12  # valor padrão de segurança

    # Aba de renovação
    with tabs[5]:
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image("assets/logos.svg", width=300)
        with col2:
            st.subheader("Renovação de atas")

        # Mostrar o prazo atual
        prazo_placeholder = st.empty()
        prazo_placeholder.markdown(f"**Prazo padrão de renovação:** {prazo_renovacao_ata} meses")

        # Formulário para alterar o prazo
        with st.expander("Alterar prazo de renovação"):
            with st.form("form_alterar_prazo", border=False):
                novo_prazo = st.number_input(
                    "Novo prazo de renovação (meses)",
                    min_value=1,
                    max_value=96,
                    value=prazo_renovacao_ata
                )
                submitted = st.form_submit_button("Salvar novo prazo")
                if submitted:
                    update_config('prazo_renovacao_ata', str(novo_prazo))  # salvando como string no banco
                    st.success(f"Prazo atualizado para {novo_prazo} meses!")
                    st.rerun()

        st.markdown("---")

        try:
            # Buscar atas
            atas_response = buscar_atas(["id", "nome", "data_inicio", "categoria_ata"])
            atas_data = {ata["id"]: ata for ata in atas_response}

            if atas_data:
                # Inicialização
                relatorio_renovacao = []
                alertas_90 = []
                alertas_30 = []
                alertas_vencidas = []

                # Preenchendo os dados brutos
                for ata in atas_data.values():
                    if not ata:
                        continue

                    data_inicio = date.fromisoformat(ata["data_inicio"])
                    data_renovacao = data_inicio + relativedelta(months=prazo_renovacao_ata)
                    dias_para_renovacao = (data_renovacao - date.today()).days

                    relatorio_renovacao.append({
                        "Ata": ata["nome"],
                        "Ata ID": ata["id"],
                        "Categoria": ata["categoria_ata"],
                        "Data Início": data_inicio.strftime('%d/%m/%Y'),
                        "Data Renovação": data_renovacao.strftime('%d/%m/%Y'),
                        "Dias para renovação": dias_para_renovacao
                    })

                    alerta = {
                        "nome": ata["nome"],
                        "dias": dias_para_renovacao,
                        "categoria": ata["categoria_ata"]
                    }

                    if dias_para_renovacao < 0 and dias_para_renovacao >= -30:
                        alertas_vencidas.append(alerta)
                    elif dias_para_renovacao > 0 and dias_para_renovacao <= 30:
                        alertas_30.append(alerta)
                    elif dias_para_renovacao > 30 and dias_para_renovacao <= 90:
                        alertas_90.append(alerta)

                # Criar DataFrame
                relatorio_df = pd.DataFrame(relatorio_renovacao)
                relatorio_df = relatorio_df[relatorio_df["Dias para renovação"] >= -30]

                # Seleção de categorias
                categorias_selecionadas = st.multiselect("Escolha a(s) categoria(s)", categorias, placeholder="Selecione", key="selecionar_categoria_renovacao")

                if categorias_selecionadas:
                    relatorio_filtrado = relatorio_df[relatorio_df["Categoria"].isin(categorias_selecionadas)]
                    st.dataframe(relatorio_filtrado, height=150)


                    def exibir_alertas(alertas):
                        alertas_filtrados = [a for a in alertas if a["categoria"] in categorias_selecionadas]
                        
                        if alertas_filtrados:
                            for a in alertas_filtrados:
                                if a["dias"] < 0:
                                    st.write(f"**Ata:** {a['nome']} — Vencida há {-a['dias']} dia(s)")
                                else:
                                    st.write(f"**Ata:** {a['nome']} — {a['dias']} dias restantes")
                        else:
                            st.write("Não há atas nesta condição.")


                    with st.container(border=True):
                        st.markdown("""
                            <div style='background-color:#aaee99; padding:17px; border-radius:7px; position:relative; margin-bottom:1em'>
                                🔔 Renovações nos próximos 90 dias:
                            </div>
                            """, unsafe_allow_html=True)
                        exibir_alertas(alertas_90)
                    
                    with st.container(border=True):
                        st.markdown("""
                            <div style='background-color:#f7f090; padding:17px; border-radius:7px; position:relative; margin-bottom:1em'>
                                ⚠️ Renovações nos próximos 30 dias:
                            </div>
                            """, unsafe_allow_html=True)
                        exibir_alertas(alertas_30)

                    with st.container(border=True):
                        st.markdown("""
                            <div style='background-color:#f8d7da; padding:17px; border-radius:7px; position:relative; margin-bottom:1em'>
                                ❌ Atas com renovação vencida:
                                <span style='float:right; cursor:help;' title='Atas com renovação vencida há mais de 30 dias não são mostradas.'>ℹ️</span>
                            </div>
                            """, unsafe_allow_html=True)
                        exibir_alertas(alertas_vencidas)
                        
                    
            else:
                st.info("Nenhuma ata cadastrada ainda.")

        except Exception as e:
            st.error(f"Erro ao gerar relatório: {e}")
