cat > app_ui.py << 'EOF'
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import websocket
import json
import threading
import time
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Price Monitor", page_icon="📊", layout="wide")

API_URL = "http://localhost:8000"

# --- GERENCIAMENTO DE SESSÃO (LOGIN) ---
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "ws_connected" not in st.session_state:
    st.session_state.ws_connected = False

# --- FUNÇÕES DE AUTENTICAÇÃO ---
def login_user(username, password):
    response = requests.post(f"{API_URL}/auth/token", data={"username": username, "password": password})
    if response.status_code == 200:
        st.session_state.token = response.json()["access_token"]
        st.session_state.username = username
        return True
    return False

def register_user(username, email, password):
    response = requests.post(f"{API_URL}/auth/register", json={"username": username, "email": email, "password": password})
    return response.status_code == 200

def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

# --- CLIENTE WEBSOCKET (RODA EM BACKGROUND) ---
def on_message(ws, message):
    st.toast(f"🔔 {message}", icon="💰")

def on_error(ws, error):
    st.error(f"WebSocket error: {error}")

def on_close(ws, close_status_code, close_msg):
    st.session_state.ws_connected = False

def on_open(ws):
    st.session_state.ws_connected = True
    st.toast("🟢 Conectado ao servidor de alertas!")

def start_websocket():
    if st.session_state.token and not st.session_state.ws_connected:
        # Pega o user_id (precisamos de um endpoint /me ou extrair do token, vamos simular com 1)
        # Na prática, você faria um GET /users/me. Vamos usar ID 1 para teste.
        ws = websocket.WebSocketApp(f"ws://localhost:8000/ws/1",
                                    on_open=on_open,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        wst = threading.Thread(target=ws.run_forever, daemon=True)
        wst.start()

# --- INTERFACE DE LOGIN ---
if not st.session_state.token:
    st.title("🔐 Bem-vindo ao Monitor de Preços")
    tab1, tab2 = st.tabs(["Login", "Cadastrar"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Usuário")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                if login_user(username, password):
                    st.success("Login realizado!")
                    start_websocket()
                    st.rerun()
                else:
                    st.error("Credenciais inválidas")
    
    with tab2:
        with st.form("register_form"):
            new_user = st.text_input("Usuário")
            new_email = st.text_input("Email")
            new_pass = st.text_input("Senha", type="password")
            if st.form_submit_button("Cadastrar"):
                if register_user(new_user, new_email, new_pass):
                    st.success("Cadastrado! Faça login.")
                else:
                    st.error("Erro no cadastro")
    st.stop()

# --- APP PRINCIPAL (LOGADO) ---
# Inicia WebSocket se não estiver conectado
if st.session_state.token and not st.session_state.ws_connected:
    start_websocket()

st.sidebar.title(f"👋 Olá, {st.session_state.username}")
if st.sidebar.button("Sair"):
    st.session_state.token = None
    st.rerun()

st.title("📊 Dashboard de Preços")

# Sidebar para adicionar produto
with st.sidebar:
    st.subheader("➕ Novo Produto")
    url = st.text_input("URL do Mercado Livre")
    target = st.number_input("Preço Alvo (R$)", min_value=0.0, step=1.0)
    if st.button("🚀 Monitorar"):
        if url:
            try:
                response = requests.post(f"{API_URL}/products/", params={"url": url, "target_price": target}, headers=get_headers())
                if response.status_code == 200:
                    st.success("✅ Adicionado!")
                    st.rerun()
                else:
                    st.error(f"Erro: {response.text}")
            except:
                st.error("Erro de conexão com a API.")

# Carrega produtos
try:
    response = requests.get(f"{API_URL}/products/", headers=get_headers())
    if response.status_code == 200:
        products = response.json()
        if not products:
            st.info("Nenhum produto sendo monitorado.")
        else:
            df = pd.DataFrame(products)
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            col1.metric("Total de Produtos", len(df))
            col2.metric("Usuário", st.session_state.username)
            col3.metric("Última Atualização", datetime.now().strftime("%H:%M"))

            # Lista de produtos (Cards)
            for idx, row in df.iterrows():
                with st.container(border=True):
                    c1, c2, c3 = st.columns([4, 2, 1])
                    c1.write(f"**{row['title']}**")
                    # Busca o último preço (vamos fazer uma requisição extra ou deixar placeholder)
                    c2.write(f"💰 R$ {row.get('target_price', 0):.2f} (Meta)")
                    if c3.button("📈 Histórico", key=row['id']):
                        st.session_state['selected_id'] = row['id']            
            
            # Gráfico (se selecionado)
            if 'selected_id' in st.session_state:
                st.divider()
                st.subheader(f"Histórico do Produto ID {st.session_state['selected_id']}")
                # Placeholder (aqui você faria GET /products/{id}/prices/)
                fake_dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
                fake_prices = [100, 95, 98, 97, 85, 82, 80, 78, 75, 72]
                fig = px.line(x=fake_dates, y=fake_prices, title="Variação de Preço", markers=True)
                st.plotly_chart(fig, use_container_width=True)
except requests.exceptions.ConnectionError:
    st.error("🚨 API não está rodando!")
EOF