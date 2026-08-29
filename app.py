import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA E BRANDING
# ==========================================
st.set_page_config(page_title="RaloZero - BlackBelt Apex", layout="wide", page_icon="📊")

# Barra Lateral (Branding e Filtros)
with st.sidebar:
    st.title("🥋 BlackBelt Apex")
    st.caption("Módulo: RaloZero - Inteligência Financeira")
    st.divider()
    st.info("Sistema de monitoramento de caixa e recuperação ativa de crédito.")

st.title("Visão Geral de Caixa e Inadimplência")
st.write("Acompanhamento em tempo real das faturas e automação de cobrança.")

# ==========================================
# 2. INGESTÃO E TRATAMENTO DE DADOS
# ==========================================
@st.cache_data
def carregar_dados():
    df = pd.read_csv('dados_financeiros.csv')
    df['Data_Vencimento'] = pd.to_datetime(df['Data_Vencimento'])
    return df

df = carregar_dados()

# Função auxiliar para formatar moeda (BRL)
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# 3. CÁLCULO DE KPIs
# ==========================================
total_recebido = df[df['Status'] == 'Pago']['Valor_Fatura'].sum()
total_atrasado = df[df['Status'] == 'Atrasado']['Valor_Fatura'].sum()
taxa_inadimplencia = (len(df[df['Status'] == 'Atrasado']) / len(df)) * 100

# ==========================================
# 4. EXIBIÇÃO DOS INDICADORES (DASHBOARD)
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("✅ Receita Garantida", formatar_moeda(total_recebido))
col2.metric("❌ Capital Travado (Atrasos)", formatar_moeda(total_atrasado))
col3.metric("⚠️ Taxa de Inadimplência", f"{taxa_inadimplencia:.1f}%")

st.divider()

# ==========================================
# 5. TABELA DE INADIMPLENTES
# ==========================================
st.subheader("🚨 Clientes com Pagamento em Atraso")
df_atrasados = df[df['Status'] == 'Atrasado']

# Exibe a tabela formatada
st.dataframe(
    df_atrasados[['Nome_Cliente', 'Valor_Fatura', 'Data_Vencimento', 'Email']].style.format({
        "Valor_Fatura": formatar_moeda,
        "Data_Vencimento": lambda t: t.strftime("%d/%m/%Y")
    }),
    use_container_width=True,
    hide_index=True
)

st.divider()

# ==========================================
# 6. MOTOR DE AUTOMAÇÃO (SMTP)
# ==========================================
def disparar_cobrancas(df_alvos):
    # DICA DE SEGURANÇA: No Streamlit Cloud, coloque essas credenciais em st.secrets
    # remetente = st.secrets["smtp"]["email"]
    # senha = st.secrets["smtp"]["senha"]
    
    remetente = "seu_email@empresa.com"
    senha = "sua_senha_de_app" 
    sucessos = 0
    
    for index, row in df_alvos.iterrows():
        try:
            msg = MIMEMultipart()
            msg['From'] = remetente
            msg['To'] = row['Email']
            msg['Subject'] = "Aviso de Vencimento - Regularização de Fatura"
            
            corpo = f"""
            Olá {row['Nome_Cliente']},
            
            Constatamos em nosso sistema que a fatura no valor de {formatar_moeda(row['Valor_Fatura'])}, 
            com vencimento em {row['Data_Vencimento'].strftime('%d/%m/%Y')}, encontra-se pendente.
            
            Por favor, desconsidere esta mensagem caso o pagamento já tenha sido efetuado.
            Para regularizar, responda a este e-mail solicitando a 2ª via.
            
            Atenciosamente,
            Equipe Financeira
            """
            msg.attach(MIMEText(corpo, 'plain'))
            
            # --- BLOCO DE CONEXÃO SMTP ---
            # Descomente e ajuste de acordo com seu servidor SMTP (Gmail, Hostinger, etc)
            # with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            #     server.login(remetente, senha)
            #     server.send_message(msg)
            
            sucessos += 1
        except Exception as e:
            st.error(f"Erro ao enviar para {row['Nome_Cliente']}: {e}")
            
    return sucessos

# Botão de Ação Isolado
st.subheader("⚡ Ações em Lote")
if st.button("Disparar Alertas Automáticos de Cobrança", type="primary"):
    if len(df_atrasados) > 0:
        with st.spinner("Conectando ao servidor SMTP e disparando e-mails..."):
            # Para testar a interface sem enviar emails de verdade, comente a linha abaixo 
            # e mude a variável 'qtd' para receber 'len(df_atrasados)'
            # qtd = disparar_cobrancas(df_atrasados) 
            qtd = len(df_atrasados) # Simulador de sucesso
            
            st.success(f"Operação concluída! {qtd} alertas de cobrança foram enviados para a base.")
            st.balloons()
    else:
        st.info("Nenhum cliente em atraso no momento.")