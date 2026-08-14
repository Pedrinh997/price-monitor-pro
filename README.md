# 📊 Price Monitor PRO

**Price Monitor PRO** is a complete price monitoring application for Mercado Livre products.  
It combines a robust API (FastAPI) with an elegant interface (NiceGUI), JWT authentication, asynchronous scraping, and automatic scheduling.

## 🚀 Tech Stack
- **Back-end:** FastAPI, SQLAlchemy (async), PostgreSQL
- **Front-end:** NiceGUI (Material Design, 100% Python)
- **Scraping:** HTTPX + BeautifulSoup
- **Authentication:** JWT + Bcrypt
- **Scheduling:** APScheduler
- **Infra:** Docker, Docker Compose (soon)

## ✨ Features
- 🔐 User registration and login (JWT)
- 🛒 Add products via Mercado Livre URL
- 📉 Price history with interactive charts (Plotly)
- ⏰ Scheduler that updates prices every 30 minutes
- 🔔 Alerts when price reaches target
- 📡 WebSockets for real-time notifications

## ▶️ How to Run (without Docker)

```bash
# 1. Clone the repository
git clone https://github.com/Pedrinh997/monitor_precos.git
cd monitor_precos

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\Activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start PostgreSQL via Docker
docker run --name postgres -e POSTGRES_PASSWORD=123456 -p 5432:5432 -d postgres:15

# 5. Create tables
python create_tables.py

# 6. Run the API (Terminal 1)
uvicorn app.main:app --reload --host 0.0.0.0

# 7. Run the interface (Terminal 2)
python app_nice.py
```

## 🌐 Access
- Interface: `http://localhost:8081`
- API (Swagger): `http://localhost:8000/docs`

## 🐳 Running with Docker (Recommended for production)
*(Coming soon)*

## 📸 Screenshots
<!-- Add a screenshot of the interface here -->
![Dashboard](screenshot.png)

## 📝 License
MIT

## 👤 Author
Pedrinh997