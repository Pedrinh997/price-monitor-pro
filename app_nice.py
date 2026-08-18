import os
import requests
from nicegui import ui
import plotly.express as px
import pandas as pd

API_URL = os.getenv("API_URL", "http://localhost:8000")

class Session:
    token = None
    username = None
    products = []
    selected_product_id = None

session = Session()

def get_headers():
    if session.token:
        return {"Authorization": f"Bearer {session.token}"}
    return {}

def api_request(method, endpoint, **kwargs):
    url = f"{API_URL}{endpoint}"
    headers = kwargs.pop("headers", {})
    if session.token:
        headers.update(get_headers())
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        ui.notify(f"Erro: {e}", type="negative")
        return None

def login_page():
    ui.page_title("Login - Price Monitor")
    with ui.column().classes("absolute-center items-center w-96"):
        ui.label("🔐 Price Monitor").classes("text-3xl font-bold mb-4")
        with ui.card().classes("w-full p-6"):
            username = ui.input("Usuário").props("outlined").classes("w-full")
            password = ui.input("Senha", password=True).props("outlined").classes("w-full")
            ui.button("Entrar", on_click=lambda: do_login(username.value, password.value)) \
                .props("color=primary").classes("w-full mt-2")
            ui.button("Cadastrar-se", on_click=lambda: register_page()).props("flat").classes("w-full")

def register_page():
    ui.page_title("Cadastro - Price Monitor")
    with ui.column().classes("absolute-center items-center w-96"):
        ui.label("📝 Criar conta").classes("text-2xl font-bold mb-4")
        with ui.card().classes("w-full p-6"):
            username = ui.input("Usuário").props("outlined").classes("w-full")
            email = ui.input("E-mail").props("outlined").classes("w-full")
            password = ui.input("Senha", password=True).props("outlined").classes("w-full")
            ui.button("Cadastrar", on_click=lambda: do_register(username.value, email.value, password.value)) \
                .props("color=primary").classes("w-full mt-2")
            ui.button("Voltar", on_click=lambda: login_page()).props("flat").classes("w-full")

def do_login(username, password):
    response = requests.post(f"{API_URL}/auth/token", data={"username": username, "password": password})
    if response.status_code == 200:
        session.token = response.json()["access_token"]
        session.username = username
        ui.notify(f"Bem-vindo, {username}!", type="positive")
        main_page()
    else:
        ui.notify("Credenciais inválidas", type="negative")

def do_register(username, email, password):
    response = requests.post(f"{API_URL}/auth/register", json={"username": username, "email": email, "password": password})
    if response.status_code == 200:
        ui.notify("Cadastro realizado! Faça login.", type="positive")
        login_page()
    else:
        ui.notify("Erro no cadastro. Tente outro usuário.", type="negative")

def main_page():
    ui.page_title("Dashboard - Price Monitor")
    with ui.header(elevated=True).classes("items-center justify-between p-4"):
        ui.label(f"📊 Price Monitor – {session.username}").classes("text-h5 text-white")
        ui.button("Sair", on_click=lambda: logout()).props("flat color=white")

    load_products()
    with ui.column().classes("w-full max-w-7xl mx-auto p-8"):
        with ui.row().classes("w-full gap-4 mb-4"):
            ui.card().classes("w-1/3 p-4").props("elevated").add_slot("default") \
                .add(ui.label("Total de produtos").classes("text-sm text-gray-500")) \
                .add(ui.label(str(len(session.products))).classes("text-2xl font-bold"))

        with ui.card().classes("w-full p-4 mb-4"):
            ui.label("➕ Adicionar novo produto").classes("text-lg font-semibold")
            with ui.row().classes("w-full gap-4 items-end"):
                url_input = ui.input("URL do Mercado Livre").props("outlined").classes("flex-grow")
                target_input = ui.number("Preço alvo", min=0).props("outlined").classes("w-48")
                ui.button("Monitorar", on_click=lambda: add_product(url_input.value, target_input.value)) \
                    .props("color=primary").classes("self-end")

        ui.label("📋 Produtos monitorados").classes("text-2xl font-bold mt-8 mb-4")
        if not session.products:
            ui.label("Nenhum produto cadastrado ainda.").classes("text-gray-500")
        else:
            with ui.grid(columns=3).classes("w-full gap-4"):
                for product in session.products:
                    with ui.card().classes("p-4").props("elevated"):
                        ui.label(product.get("title", "Sem título")).classes("text-lg font-semibold")
                        ui.label(f"💰 Preço alvo: R$ {product.get('target_price', 0):.2f}").classes("text-sm")
                        ui.label(f"🆔 ID: {product['id']}").classes("text-xs text-gray-400")
                        with ui.row().classes("w-full justify-end gap-2 mt-2"):
                            ui.button("Histórico", on_click=lambda p=product: load_history(p["id"])) \
                                .props("outline size=sm")

        if session.selected_product_id:
            ui.separator().classes("my-8")
            ui.label("📈 Histórico de preços").classes("text-xl font-bold")
            history = api_request("GET", f"/products/{session.selected_product_id}/prices/")
            if history and len(history) > 0:
                df = pd.DataFrame(history)
                df["scraped_at"] = pd.to_datetime(df["scraped_at"])
                fig = px.line(df, x="scraped_at", y="price", markers=True)
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
                ui.plotly(fig).classes("w-full")
            else:
                ui.label("Nenhum histórico disponível.").classes("text-gray-500")
            session.selected_product_id = None

def load_products():
    data = api_request("GET", "/products/")
    if data is not None:
        session.products = data

def add_product(url, target_price):
    if not url:
        ui.notify("URL é obrigatória", type="warning")
        return
    params = {"url": url}
    if target_price is not None:
        params["target_price"] = target_price
    result = api_request("POST", "/products/", params=params)
    if result:
        ui.notify(f"Produto adicionado: {result.get('title', '')}", type="positive")
        load_products()
        ui.navigate.reload()

def load_history(product_id):
    session.selected_product_id = product_id
    ui.navigate.reload()

def logout():
    session.token = None
    session.username = None
    session.products = []
    session.selected_product_id = None
    ui.navigate.to("/")
    ui.notify("Desconectado", type="info")
    login_page()

# --- PONTO DE ENTRADA (MODIFICADO PARA RAILWAY) ---
login_page()
port = int(os.getenv("PORT", 8081))
ui.run(title="Price Monitor", port=port, host="0.0.0.0", reload=False)
