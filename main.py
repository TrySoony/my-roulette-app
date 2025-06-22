import logging
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types, F
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

# События приложения
@app.on_event("startup")
async def on_startup():
    """Действия при запуске приложения"""
    logger.info("Starting up...")
    webhook_url = f"{config.webhook_url}/webhook"
    webhook_info = await bot.get_webhook_info()
    
    if webhook_info.url != webhook_url:
        logger.info(f"Setting webhook to {webhook_url}")
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )

@app.on_event("shutdown")
async def on_shutdown():
    """Действия при остановке приложения"""
    logger.info("Shutting down...")
    await bot.session.close()

# Обработчики команд бота
@dp.message(F.text == "/start")
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    try:
        await message.answer(
            "Привет! Я бот для розыгрыша призов. Нажми на кнопку ниже, чтобы открыть рулетку.",
            reply_markup=types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="🎲 Открыть рулетку",
                        web_app=types.WebAppInfo(url=f"{config.webhook_url}")
                    )]
                ]
            )
        )
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@dp.message(F.text == "/help")
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    try:
        await message.answer(
            "🎮 Как играть:\n\n"
            "1. Нажмите кнопку 'Открыть рулетку'\n"
            "2. Крутите колесо и выигрывайте призы\n"
            "3. Собирайте коллекцию подарков\n\n"
            "У вас есть 2 попытки в день. Удачи! 🍀"
        )
    except Exception as e:
        logger.error(f"Error in help command: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

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