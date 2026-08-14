from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from . import scraper, models, database
from sqlalchemy import select
import asyncio

def update_all_prices():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_update_prices())

async def async_update_prices():
    async with database.AsyncSessionLocal() as db:
        # Usa select() em vez de query()
        stmt = select(models.Product)
        result = await db.execute(stmt)
        products = result.scalars().all()

        for product in products:
            try:
                data = await scraper.scrape_product(product.url)
                price_entry = models.PriceHistory(
                    product_id=product.id,
                    price=data["price"],
                    currency=data["currency"]
                )
                db.add(price_entry)
                if product.target_price and data["price"] < product.target_price:
                    print(f"🔔 ALERTA: {product.title} caiu para R$ {data['price']}!")
            except Exception as e:
                print(f"❌ Erro no scraping de {product.url}: {e}")
        await db.commit()

scheduler = BackgroundScheduler()
scheduler.add_job(update_all_prices, trigger=IntervalTrigger(minutes=1))  # 1 minuto para teste
scheduler.start()