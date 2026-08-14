from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from .database import engine, Base, get_db
from . import models, schemas, scraper, auth
from .routes import auth as auth_routes
from .websocket_manager import manager
from .scheduler import scheduler
import asyncio

# As tabelas já foram criadas via create_tables.py
# Não é necessário recriá-las aqui com AsyncEngine
# Base.metadata.create_all(bind=engine)

app = FastAPI(title="Price Monitor PRO", version="3.0.0")

# Inclui as rotas de autenticação
app.include_router(auth_routes.router)

@app.on_event("startup")
async def startup():
    print("🚀 Scheduler iniciado. Atualizando preços a cada 1 minuto (teste).")

@app.get("/")
def root():
    return {"message": "Price Monitor PRO com Auth, Scheduler e WebSocket!"}

@app.post("/scrape")
async def scrape(request: schemas.ScrapeRequest):
    try:
        return await scraper.scrape_product(str(request.url))
    except Exception as e:
        raise HTTPException(500, detail=str(e))

# --- ROTAS DE PRODUTO (com usuário autenticado) ---
@app.post("/products/")
async def add_product(
    url: str,
    target_price: float = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    try:
        scraped = await scraper.scrape_product(url)
    except Exception as e:
        raise HTTPException(400, detail=f"Erro ao raspar: {str(e)}")

    new_product = models.Product(
        url=url,
        title=scraped["title"],
        target_price=target_price,
        owner_id=current_user.id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    price_entry = models.PriceHistory(
        product_id=new_product.id,
        price=scraped["price"],
        currency=scraped["currency"]
    )
    db.add(price_entry)
    db.commit()

    return new_product

@app.get("/products/")
def list_products(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.Product).filter(models.Product.owner_id == current_user.id).all()

@app.get("/products/{product_id}/prices/")
def get_prices(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return db.query(models.PriceHistory).filter(models.PriceHistory.product_id == product_id).all()

# --- WEBSOCKET ---
@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # mantém a conexão aberta
    except WebSocketDisconnect:
        manager.disconnect(websocket)