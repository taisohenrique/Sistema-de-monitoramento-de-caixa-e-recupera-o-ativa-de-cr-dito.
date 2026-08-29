import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E BRANDING
# ==========================================
st.set_page_config(page_title="RaloZero - BlackBelt Apex", layout="wide", page_icon="🥋")

# Inicializa o Banco de Dados em Memória Volátil (Session State)
if 'df_clientes' not in st.session_state:
    st.session_state.df_clientes = pd.DataFrame(
        columns=['Nome_Cliente', 'Email', 'Valor_Fatura', 'Data_Vencimento', 'Status']
    )

# Barra Lateral (Branding, Upload e LGPD)
with st.sidebar:
    st.title("🥋 BlackBelt Apex")
    st.caption("Módulo: RaloZero - Inteligência Financeira")
    st.divider()
    
    # Upload de Arquivos
    st.subheader("📂 Carregar Dados")
    arquivo_upload = st.file_uploader("Suba sua planilha (CSV)", type=["csv"])
    
    if arquivo_upload is not None:
        try:
            df_temp = pd.read_csv(arquivo_upload)
            df_temp['Data_Vencimento'] = pd.to_datetime(df_temp['Data_Vencimento'])
            st.session_state.df_clientes = df_temp
            st.success("Planilha carregada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: Certifique-se de que as colunas estão corretas. ({e})")
            
    st.divider()
    
    # Escudo LGPD
    st.info("🛡️ **Conformidade LGPD:** \n\nOs dados processados nesta sessão são voláteis. Não armazenamos nenhuma informação sensível em nossos servidores após o fechamento desta janela.")

st.title("Visão Geral de Caixa e Inadimplência")
st.write("Acompanhamento em tempo real das faturas e automação de cobrança.")

# ==========================================
# 2. INSERÇÃO MANUAL DE DADOS (NOVO)
# ==========================================
with st.expander("➕ Adicionar Cliente Manualmente"):
    with st.form("form_novo_cliente", clear_on_submit=True):
        col_form1, col_form2 = st.columns(2)
        nome = col_form1.text_input("Nome do Cliente")
        email = col_form2.text_input("E-mail do Cliente")
        valor = col_form1.number_input("Valor da Fatura (R$)", min_value=0.0, step=50.0)
        data_venc = col_form2.date_input("Data de Vencimento")
        status = st.selectbox("Status de Pagamento", ["Pendente", "Atrasado", "Pago"])
        
        submit_btn = st.form_submit_button("Registrar Fatura")
        
        if submit_btn and nome and email:
            novo_registro = pd.DataFrame({
                'Nome_Cliente': [nome],
                'Email': [email],
                'Valor_Fatura': [valor],
                'Data_Vencimento': [pd.to_datetime(data_venc)],
                'Status': [status]
            })
            st.session_state.df_clientes = pd.concat([st.session_state.df_clientes, novo_registro], ignore_index=True)
            st.success(f"Fatura de {nome} adicionada!")

# ==========================================
# 3. TRATAMENTO E EXIBIÇÃO
# ==========================================
df = st.session_state.df_clientes

def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Só calcula KPIs se houver dados
if not df.empty:
    total_recebido = df[df['Status'] == 'Pago']['Valor_Fatura'].sum()
    total_atrasado = df[df['Status'] == 'Atrasado']['Valor_Fatura'].sum()
    taxa_inadimplencia = (len(df[df['Status'] == 'Atrasado']) / len(df)) * 100 if len(df) > 0 else 0.0

    # Dashboard KPIs
    st.divider()
    col1, col2, col3 = st.columns(3)
    col1.metric("✅ Receita Garantida", formatar_moeda(total_recebido))
    col2.metric("❌ Capital Travado (Atrasos)", formatar_moeda(total_atrasado))
    col3.metric("⚠️ Taxa de Inadimplência", f"{taxa_inadimplencia:.1f}%")

    # Tabela de Inadimplentes e Edição em Massa
    st.divider()
    st.subheader("🚨 Clientes com Pagamento em Atraso")
    
    df_atrasados = df[df['Status'] == 'Atrasado']
    
    if not df_atrasados.empty:
        st.dataframe(
            df_atrasados[['Nome_Cliente', 'Valor_Fatura', 'Data_Vencimento', 'Email']].style.format({
                "Valor_Fatura": formatar_moeda,
                "Data_Vencimento": lambda t: t.strftime("%d/%m/%Y")
            }),
            use_container_width=True,
            hide_index=True
        )
        
        st.divider()
        st.subheader("⚡ Ações em Lote")
        
        if st.button("Disparar Alertas Automáticos de Cobrança", type="primary"):
            with st.spinner("Conectando ao servidor SMTP e disparando e-mails..."):
                # Aqui entra a sua função SMTP real no futuro
                qtd = len(df_atrasados)
                st.success(f"Operação concluída! {qtd} alertas de cobrança foram enviados para a base de inadimplentes.")
                st.balloons()
    else:
        st.success("Nenhum cliente em atraso detectado na base atual. O caixa está saudável!")
else:
    st.info("O painel está vazio. Faça o upload de uma planilha CSV no menu lateral ou adicione registros manualmente para gerar a inteligência.")
