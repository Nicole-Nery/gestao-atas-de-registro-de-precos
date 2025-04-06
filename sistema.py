import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import psycopg2

def conectar (): 
    return psycopg2.connect(
        host = "localhost",
        port = "5433",
        dbname = "grpdb",
        user = "postgres",
        password = "mypassword"
    )

# Alterando o nome da página e o ícone
st.set_page_config(page_title= "Gestão de ARP", 
                   page_icon= "📄")
st.title("Sistema de Gestão de Atas de Registro de Preços")
st.write("Bem-vindo ao sistema de controle de atas, onde você pode gerenciar saldos, acompanhar validade e gerar relatórios.")

# Estabelecendo o layout com abas
tabs = st.tabs(["Cadastro de Fornecedores", "Registro de Atas", "Registro de Empenhos", "Histórico de Empenhos", "Relatórios"])

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

    if submit_fornecedor and nome_fornecedor and cnpj: # Itens obrigatórios para que o fornecedor possa ser cadastrado
        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                        INSERT INTO fornecedores (nome, cnpj, email, endereco, telefone) VALUES (%s, %s, %s, %s, %s)""", 
                        (nome_fornecedor, cnpj, email, endereco, telefone))
            
            conn.commit()
            st.success(f"Fornecedor '{nome_fornecedor}' cadastrado com sucesso!")
        
        except Exception as e:
            st.error(f"Erro ao cadastrar fornecedor: {e}.")
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

    # Listagem de fornecedores
    st.subheader("Fornecedores cadastrados")
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT nome, cnpj, email, endereco, telefone FROM fornecedores ORDER BY nome")
        fornecedores_result = cursor.fetchall()
        
        df_fornecedores = pd.DataFrame(fornecedores_result, columns=["Nome", "CNPJ", "E-mail", "Endereço", "Telefone"])
        st.dataframe(df_fornecedores)

        conn.close()

    except Exception as e:
        st.error(f"Erro ao buscar fornecedor: {e}.")

    
# Registro de Atas
with tabs[1]:
    st.header("Registro de Atas")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM fornecedores ORDER BY nome;")
    fornecedores_result = cursor.fetchall()
    cursor.close()

    fornecedores_dict = {nome: id_ for id_, nome in fornecedores_result}
    fornecedores_cadastrados = ["Selecione"] + list(fornecedores_dict.keys())

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
                    cursor = conn.cursor()
                    cursor.execute("""INSERT INTO atas (nome, data_inicio, data_validade, fornecedor_id, link_ata) VALUES (%s, %s, %s, %s, %s);""", (nome_ata, data_ata, validade_ata, fornecedor_id, link_ata))
                    conn.commit()
                    st.success(f"Ata '{nome_ata}' cadastrada com sucesso!")

                except Exception as e:
                    conn.rollback()
                    st.error(f"Erro ao cadastrar a Ata: {e}")

                finally:
                    cursor.close()
                    conn.close()
            

    # Adicionando Equipamentos à Ata
    st.subheader("Cadastrar Equipamentos para a Ata")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM atas ORDER BY nome;")
    atas_result = cursor.fetchall()
    
    atas_dict = {nome: id_ for id_, nome in atas_result}
    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

    ata_nome = st.selectbox("Selecione a Ata", atas_cadastradas, key="selecione_ata_nome")

    if ata_nome != "Selecione":
        ata_id = atas_dict[ata_nome]

        with st.form("novo_equipamento", clear_on_submit=True):
            st.subheader("Adicionar Equipamento")

            especificacao = st.text_input("Especificação")
            marca_modelo = st.text_input("Marca/Modelo")
            quantidade = st.number_input("Quantidade", min_value=1, step=1)
            saldo_disponivel = st.number_input("Saldo disponível", min_value=0, step=1)
            valor_unitario = st.number_input("Valor Unitário", min_value=0.0, format="%.2f")
            valor_total = valor_unitario * quantidade
            submit_equipamento = st.form_submit_button("Adicionar Equipamento")

            if submit_equipamento and especificacao and marca_modelo and quantidade and saldo_disponivel and valor_unitario:
                try:
                    cursor.execute("""INSERT INTO equipamentos (ata_id, especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario, valor_total) VALUES (%s, %s, %s, %s, %s, %s, %s)""", (ata_id, especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario, valor_total)) 
                    conn.commit()
                    st.success(f"Equipamento '{especificacao}' cadastrado com sucesso na ata {ata_nome}!")   

                except Exception as e:
                     conn.rollback()
                     st.error(f"Erro ao cadastrar equipamento: {e}.")
        
    # Visualização dos dados cadastrados na Ata selecionada
    st.subheader("Visualizar Atas Cadastradas")

    # Buscando todas as atas
    cursor.execute("""
        SELECT a.id, a.nome, a.data_inicio, a.data_validade, a.link_ata, f.nome AS fornecedor
        FROM atas a
        JOIN fornecedores f ON a.fornecedor_id = f.id
        ORDER BY a.data_inicio DESC
        """)
    atas_result = cursor.fetchall()
    atas_dict = {nome: id_ for id_, nome, *_ in atas_result}
    atas_opcoes = ["Selecione"] + list(atas_dict.keys())

    ata_visualizar = st.selectbox("Selecione uma Ata para visualizar", atas_opcoes, key="selecione_ata_visualizar")

    if ata_visualizar != "Selecione":
        ata_id = atas_dict[ata_visualizar]

        # Buscar dados da Ata selecionada
        cursor.execute("""
            SELECT a.nome, a.data_inicio, a.data_validade, a.link_ata, f.nome
            FROM atas a
            JOIN fornecedores f ON a.fornecedor_id = f.id
            WHERE a.id = %s
        """, (ata_id,))
        ata_info = cursor.fetchone()

        nome, data_ata, validade_ata, link_pdf, fornecedor_nome = ata_info

        st.markdown(f"**Nome:** {nome}")
        st.markdown(f"**Data da Ata:** {data_ata.strftime('%d/%m/%Y')}")
        st.markdown(f"**Validade:** {validade_ata.strftime('%d/%m/%Y')}")
        st.markdown(f"**Fornecedor:** {fornecedor_nome}")
        if link_pdf:
            st.markdown(f"[Abrir PDF da Ata]({link_pdf})", unsafe_allow_html=True)

        # Buscar e exibir equipamentos da Ata
        st.subheader("Equipamentos Cadastrados")
        cursor.execute("""
            SELECT especificacao, marca_modelo, quantidade, saldo_disponivel, valor_unitario, valor_total
            FROM equipamentos
            WHERE ata_id = %s
        """, (ata_id,))
        equipamentos = cursor.fetchall()

        if equipamentos:
            df_equip = pd.DataFrame(equipamentos, columns=["Especificação", "Marca/Modelo", "Quantidade", "Saldo Disponível", "Valor Unitário", "Valor Total"])
            st.dataframe(df_equip)
        else:
            st.info("Nenhum equipamento cadastrado para esta Ata.")

                
# Registro de Empenhos
with tabs[2]:
    st.header("Registro de Empenhos")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome FROM atas ORDER BY nome;")
    atas_result = cursor.fetchall()

    atas_dict = {nome: id_ for id_, nome in atas_result}
    atas_cadastradas = ["Selecione"] + list(atas_dict.keys())

    ata_nome = st.selectbox("Selecione a Ata", atas_cadastradas, key="selecione_ata_nome_empenho")

    if ata_nome != "Selecione":
        ata_id = atas_dict[ata_nome]

        cursor.execute("""SELECT id, especificacao, saldo_disponivel FROM equipamentos WHERE ata_id = %s AND saldo_disponivel > 0""", (ata_id,))
        equipamentos_result = cursor.fetchall()

        if equipamentos_result:
            equipamentos_dict = {especificacao: (id, saldo_disponivel) for id, especificacao, saldo_disponivel in equipamentos_result}
            equip_opcoes = ["Selecione"] + list(equipamentos_dict.keys())

            equipamento_nome = st.selectbox("Selecione o Equipamento", equip_opcoes, key="selecione_equipamento_nome")

            if equipamento_nome != "Selecione":
                equipamento_id, saldo_disp = equipamentos_dict[equipamento_nome]
                quantidade = st.number_input("Quantidade empenhada", min_value=1, max_value=saldo_disp, step=1)
                data_empenho = st.date_input("Data do Empenho", format="DD/MM/YYYY")
                observacao = st.text_input("Observação (opcional)")

                if st.button("Registrar Empenho"):
                    try:
                        # Registrar empenho
                        cursor.execute("""INSERT INTO empenhos (equipamento_id, quantidade_empenhada, data_empenho, observacao) VALUES (%s, %s, %s, %s)""", (equipamento_id, quantidade, data_empenho, observacao))

                        # Atualizar saldo do equipamento
                        cursor.execute("""UPDATE equipamentos
                            SET saldo_disponivel = saldo_disponivel - %s
                            WHERE id = %s""", (quantidade, equipamento_id))

                        conn.commit()
                        st.success("Empenho registrado com sucesso!")

                    except Exception as e:
                        conn.rollback()
                        st.error(f"Erro ao registrar empenho: {e}")

        else:
            st.warning("Nenhum equipamento com saldo disponível para esta Ata.")

        # Exibir empenhos já registrados
        st.subheader("Empenhos Registrados para esta Ata")

        cursor.execute("""
            SELECT eq.especificacao, e.quantidade_empenhada, e.data_empenho, e.observacao
            FROM empenhos e
            JOIN equipamentos eq ON e.equipamento_id = eq.id
            WHERE eq.ata_id = %s
            ORDER BY e.data_empenho DESC
        """, (ata_id,))
        empenhos = cursor.fetchall()

        if empenhos:
            df_empenhos = pd.DataFrame(empenhos, columns=["Equipamento", "Quantidade", "Data", "Observação"])
            df_empenhos["Data"] = pd.to_datetime(df_empenhos["Data"]).dt.strftime('%d/%m/%Y')
            st.dataframe(df_empenhos)
        else:
            st.info("Nenhum empenho registrado para esta Ata.")


# Histórico de Empenhos
with tabs[3]:
    st.header("Histórico de Empenhos")

    try:
        with conn.cursor() as cur:
            # Obter lista de atas
            cur.execute("SELECT id, nome FROM atas ORDER BY nome")
            atas_result = cur.fetchall()
            atas_dict = {nome: id_ for id_, nome in atas_result}

        atas_opcoes = ["Todas"] + list(atas_dict.keys())
        ata_filtro = st.selectbox("Filtrar por Ata", atas_opcoes, key="selecione_ata_filtro")

        with conn.cursor() as cur:
            if ata_filtro != "Todas":
                ata_id = atas_dict[ata_filtro]
                cur.execute("""
                    SELECT a.nome AS ata, eq.especificacao AS equipamento, e.quantidade_empenhada, 
                           e.data_empenho, e.observacao
                    FROM empenhos e
                    JOIN equipamentos eq ON e.equipamento_id = eq.id
                    JOIN atas a ON eq.ata_id = a.id
                    WHERE a.id = %s
                    ORDER BY e.data_empenho DESC
                """, (ata_id,))
            else:
                cur.execute("""
                    SELECT a.nome AS ata, eq.especificacao AS equipamento, e.quantidade_empenhada, 
                           e.data_empenho, e.observacao
                    FROM empenhos e
                    JOIN equipamentos eq ON e.equipamento_id = eq.id
                    JOIN atas a ON eq.ata_id = a.id
                    ORDER BY e.data_empenho DESC
                """)
            empenhos_result = cur.fetchall()

        if empenhos_result:
            df_empenhos = pd.DataFrame(empenhos_result, columns=["Ata", "Equipamento", "Quantidade", "Data do Empenho", "Observação"])
            df_empenhos["Data do Empenho"] = pd.to_datetime(df_empenhos["Data do Empenho"]).dt.strftime('%d/%m/%Y')
            st.dataframe(df_empenhos)
        else:
            st.info("Nenhum empenho registrado ainda.")
    except Exception as e:
        st.error(f"Erro ao buscar empenhos: {e}")
        conn.rollback()


# Aba 4: Relatórios de Consumo e Status
with tabs[4]:
    st.header("Relatórios de Consumo e Status")

    try:
        with conn.cursor() as cur:
            # Buscar todas as atas com seus equipamentos
            cur.execute("""
                SELECT a.nome AS ata, eq.especificacao, eq.quantidade, eq.saldo_disponivel, a.data_validade
                FROM equipamentos eq
                JOIN atas a ON eq.ata_id = a.id
                ORDER BY a.data_validade
            """)
            relatorio_result = cur.fetchall()

        if relatorio_result:
            relatorio_consumo = []
            for ata, espec, qtd, saldo_disp, validade in relatorio_result:
                saldo_utilizado = qtd - saldo_disp
                relatorio_consumo.append({
                    "Ata": ata,
                    "Equipamento": espec,
                    "Saldo Utilizado": saldo_utilizado,
                    "Saldo Disponível": saldo_disp,
                    "Data de Validade": validade
                })

            relatorio_df = pd.DataFrame(relatorio_consumo)
            relatorio_df["Data de Validade"] = pd.to_datetime(relatorio_df["Data de Validade"]).dt.strftime('%d/%m/%Y')
            st.dataframe(relatorio_df)
        else:
            st.info("Nenhum consumo registrado ainda.")

        # Alerta para atas vencendo em até 7 dias
        hoje = datetime.today().date()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT nome, data_validade
                FROM atas
                WHERE data_validade <= %s
                ORDER BY data_validade
            """, (hoje + timedelta(days=7),))
            alertas = cur.fetchall()

        if alertas:
            st.warning("Alertas de vencimento de atas nos próximos 7 dias:")
            for nome, validade in alertas:
                st.write(f"**Ata:** {nome} — **Validade:** {validade}")
        else:
            st.info("Nenhuma Ata vencendo em 7 dias.")
    except Exception as e:
        st.error(f"Erro ao gerar relatório: {e}")
        conn.rollback()
