import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ==========================================
# 1. CONFIGURAÇÃO E BANCO DE DADOS (SQLITE)
# ==========================================
st.set_page_config(page_title="RaloZero - BlackBelt Apex", layout="wide", page_icon="🥋")

# Cria e conecta ao banco de dados local
conn = sqlite3.connect('ralozero_clientes.db', check_same_thread=False)
c = conn.cursor()

# Cria a tabela se não existir
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
        
        # Simulação de credenciais do cliente (Ex: Clinica Sorriso)
        if submit:
            if usuario == "admin" and senha == "blackbelt2026":
                st.session_state.autenticado = True
                st.session_state.cliente_id = "clinica_sorriso_01" # ID único do cliente
                st.rerun()
            else:
                st.error("Credenciais inválidas.")

if not st.session_state.autenticado:
    login()
    st.stop() # Interrompe a execução aqui se não estiver logado

# ==========================================
# 3. INTERFACE DO PAINEL (ÁREA LOGADA)
# ==========================================
def carregar_dados_sql(cliente_id):
    query = f"SELECT nome as Nome_Cliente, email as Email, valor as Valor_Fatura, vencimento as Data_Vencimento, status as Status FROM faturas WHERE cliente_id = '{cliente_id}'"
    df = pd.read_sql_query(query, conn)
    if not df.empty:
        df['Data_Vencimento'] = pd.to_datetime(df['Data_Vencimento'])
    return df

# Barra Lateral
with st.sidebar:
    st.title("Módulo: RaloZero")
    st.caption(f"Logado como: {st.session_state.cliente_id}")
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()
        
    st.divider()
    
    # Função de Exportação para Excel/CSV
    st.subheader("📥 Exportar Relatório")
    df_atual = carregar_dados_sql(st.session_state.cliente_id)
    if not df_atual.empty:
        csv = df_atual.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Baixar Dados em CSV (Excel)",
            data=csv,
            file_name=f"relatorio_financeiro_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
        )
    else:
        st.info("Não há dados para exportar.")

st.title("Visão Geral de Caixa e Inadimplência")

# ==========================================
# 4. INSERÇÃO E ATUALIZAÇÃO NO BANCO
# ==========================================
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
            st.success(f"Fatura de {nome} salva com sucesso!")
            st.rerun()

# ==========================================
# 5. DASHBOARD E KPIs (LENDO DO BANCO)
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
    st.info("Nenhum dado encontrado no banco. Adicione faturas para começar.")
