import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# ==========================================
# 1. CONFIGURAÇÃO E BANCO DE DADOS (SQLITE)
# ==========================================
st.set_page_config(page_title="RaloZero - BlackBelt Apex", layout="wide", page_icon="🥋")

conn = sqlite3.connect('ralozero_clientes.db', check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS faturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id TEXT,
        nome TEXT,
        email TEXT,
        valor REAL,
        vencimento DATE,
        status TEXT
    )
''')
conn.commit()

# ==========================================
# 2. SISTEMA DE AUTENTICAÇÃO (LOGIN)
# ==========================================
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def login():
    st.title("🥋 BlackBelt Apex - Acesso Restrito")
    with st.form("login_form"):
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar no Sistema")
        
        if submit:
            if usuario == "admin" and senha == "blackbelt2026":
                st.session_state.autenticado = True
                st.session_state.cliente_id = "clinica_sorriso_01"
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

if not st.session_state.autenticado:
    login()
    st.stop()

# ==========================================
# 3. FUNÇÕES DE BANCO DE DADOS
# ==========================================
def carregar_dados_sql(cliente_id):
    query = f"SELECT nome as Nome_Cliente, email as Email, valor as Valor_Fatura, vencimento as Data_Vencimento, status as Status FROM faturas WHERE cliente_id = '{cliente_id}'"
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['Data_Vencimento'] = pd.to_datetime(df['Data_Vencimento'])
    return df

def salvar_lote_sql(df_import, cliente_id):
    sucessos = 0
    for index, row in df_import.iterrows():
        c.execute("INSERT INTO faturas (cliente_id, nome, email, valor, vencimento, status) VALUES (?, ?, ?, ?, ?, ?)",
                  (cliente_id, row['Nome_Cliente'], row['Email'], row['Valor_Fatura'], row['Data_Vencimento'].date(), row['Status']))
        sucessos += 1
    conn.commit()
    return sucessos

# ==========================================
# 4. BARRA LATERAL: IMPORTAÇÃO E EXPORTAÇÃO
# ==========================================
with st.sidebar:
    st.title("Módulo: RaloZero")
    st.caption(f"Logado como: {st.session_state.cliente_id}")
    
    st.divider()
    
    # IMPORTAÇÃO DE PLANILHA
    st.subheader("⬆️ Importar Planilha")
    st.write("Suba sua base de clientes (.xlsx ou .csv)")
    arquivo_upload = st.file_uploader("", type=["csv", "xlsx"])
    
    if arquivo_upload is not None:
        if st.button("Processar e Salvar no Banco"):
            with st.spinner("Importando dados..."):
                try:
                    if arquivo_upload.name.endswith('.csv'):
                        df_temp = pd.read_csv(arquivo_upload)
                    else:
                        df_temp = pd.read_excel(arquivo_upload)
                        
                    # Padronização de datas para evitar erros no SQL
                    df_temp['Data_Vencimento'] = pd.to_datetime(df_temp['Data_Vencimento'])
                    
                    qtd_salva = salvar_lote_sql(df_temp, st.session_state.cliente_id)
                    st.success(f"{qtd_salva} registros importados com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro na importação. Verifique se as colunas estão nomeadas corretamente: Nome_Cliente, Email, Valor_Fatura, Data_Vencimento, Status. Erro técnico: {e}")

    st.divider()
    
    # EXPORTAÇÃO EM EXCEL NATIVO
    st.subheader("⬇️ Exportar Relatório")
    df_atual = carregar_dados_sql(st.session_state.cliente_id)
    if not df_atual.empty:
        # Criar arquivo Excel em memória (Buffer)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_atual.to_excel(writer, index=False, sheet_name='Relatório Financeiro')
        
        st.download_button(
            label="Baixar Dados em Excel (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"RaloZero_Export_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
    else:
        st.info("O painel está vazio.")

    st.divider()
    if st.button("Sair do Sistema"):
        st.session_state.autenticado = False
        st.rerun()

# ==========================================
# 5. PAINEL PRINCIPAL E INSERÇÃO MANUAL
# ==========================================
st.title("Visão Geral de Caixa e Inadimplência")

with st.expander("➕ Adicionar Fatura Manualmente"):
    with st.form("form_novo_cliente", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        nome = col_form1.text_input("Nome do Cliente")
        email = col_form2.text_input("E-mail do Cliente")
        valor = col_form1.number_input("Valor da Fatura (R$)", min_value=0.0, step=50.0)
        data_venc = col_form2.date_input("Data de Vencimento")
        status = st.selectbox("Status de Pagamento", ["Pendente", "Atrasado", "Pago"])
        
        if st.form_submit_button("Registrar no Banco de Dados"):
            c.execute("INSERT INTO faturas (cliente_id, nome, email, valor, vencimento, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (st.session_state.cliente_id, nome, email, valor, data_venc, status))
            conn.commit()
            st.success(f"Fatura de {nome} salva!")
            st.rerun()

# ==========================================
# 6. DASHBOARD (LEITURA EM TEMPO REAL)
# ==========================================
df = carregar_dados_sql(st.session_state.cliente_id)

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

if not df.empty:
    total_recebido = df[df['Status'] == 'Pago']['Valor_Fatura'].sum()
    total_atrasado = df[df['Status'] == 'Atrasado']['Valor_Fatura'].sum()
    taxa_inadimplencia = (len(df[df['Status'] == 'Atrasado']) / len(df)) * 100

    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Receita Garantida", formatar_moeda(total_recebido))
    col2.metric("❌ Capital Travado (Atrasos)", formatar_moeda(total_atrasado))
    col3.metric("⚠️ Taxa de Inadimplência", f"{taxa_inadimplencia:.1f}%")

    st.divider()
    st.subheader("🚨 Clientes com Pagamento em Atraso")
    
    df_atrasados = df[df['Status'] == 'Atrasado']
    
    if not df_atrasados.empty:
        st.dataframe(
            df_atrasados.style.format({
                "Valor_Fatura": formatar_moeda,
                "Data_Vencimento": lambda t: t.strftime("%d/%m/%Y") if pd.notnull(t) else ""
            }),
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("Nenhum dado encontrado no banco. Importe uma planilha ou adicione faturas manualmente para gerar inteligência.")
