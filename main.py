import logging
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types
from config import config
import api_routes
import admin_routes

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="Telegram Prize Roulette",
    description="Веб-приложение для розыгрыша призов через Telegram Web App",
    version="1.0.0",
    debug=config.debug
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory=".")

# Инициализация бота
bot = Bot(token=config.bot_token)
dp = Dispatcher()

# Подключение роутеров
app.include_router(api_routes.router)
app.include_router(admin_routes.router)

@app.get("/")
async def root(request: Request):
    """Главная страница с рулеткой"""
    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return Response(
            content="Internal Server Error",
            status_code=500
        )

@app.get("/admin")
async def admin_panel(request: Request):
    """Админ-панель"""
    try:
        return templates.TemplateResponse(
            "admin.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error rendering admin page: {e}")
        return Response(
            content="Internal Server Error",
            status_code=500
        )

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности сервиса"""
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Обработчик вебхуков от Telegram"""
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Error in webhook handler: {e}")
        return Response(status_code=500)

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    )