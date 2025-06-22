from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import json
import os
import logging
import hmac
import hashlib
import base64
from urllib.parse import parse_qs
import time
from datetime import datetime
import custom_methods
from config import config

# --- 1. Конфигурация ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from config import config
    logging.info("Configuration loaded.")
except Exception as e:
    logging.critical(f"Failed to load config: {e}", exc_info=True)
    raise

# --- 2. Инициализация ---
bot = Bot(config.bot_token)
dp = Dispatcher()
app = FastAPI(title="Roulette Bot API")

# --- 3. Управление данными пользователей ---
USER_DATA_FILE = "user_data.json"
MAX_ATTEMPTS = config.max_attempts

def read_user_data():
    if not os.path.exists(USER_DATA_FILE): return {}
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            return json.loads(content) if content else {}
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def verify_telegram_web_app_data(init_data: str) -> int:
    try:
        parsed_data = parse_qs(init_data)
        
        if 'user' not in parsed_data:
            raise ValueError("No user data in init_data")
            
        user_data = json.loads(parsed_data['user'][0])
        user_id = user_data.get('id')
        
        if not user_id:
            raise ValueError("No user ID in init_data")
            
        # Проверяем хеш
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            raise ValueError("No hash in init_data")
            
        data_check_string = '\n'.join(
            f"{key}={value[0]}" for key, value in sorted(parsed_data.items()) 
            if key != 'hash'
        )
        
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=config.bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            raise ValueError("Hash mismatch")
            
        return user_id
        
    except Exception as e:
        logging.error(f"Error verifying Telegram data: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

# --- 4. Обработка статических файлов ---
ALLOWED_FILES = [
    'index.html', 'admin.html', 'style.css', 'prizes.js', 'roulette.js', 'admin.js',
    'images/diamond_ring.png', 'images/light_sword.png', 'images/nail_bracelet.png',
    'images/easter_egg.png', 'images/neko_helmet.png', 'images/bonded_ring.png',
    'images/love_potion.png'
]

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/{filepath:path}")
async def serve_static_files(filepath: str):
    if filepath == "":
        filepath = "index.html"
    
    if filepath not in ALLOWED_FILES:
        logging.warning(f"Static file not found or not allowed: {filepath}")
        return Response(status_code=404)
    
    return FileResponse(filepath)

# --- 5. API эндпоинты ---
@app.post("/api/user")
async def announce_user(request: Request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="No user_id provided")
            
        user_data = read_user_data()
        
        if str(user_id) not in user_data:
            user_data[str(user_id)] = {
                "attempts_left": MAX_ATTEMPTS,
                "gifts": []
            }
            save_user_data(user_data)
            
        return {"status": "success"}
    except Exception as e:
        logging.error(f"Error in announce_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/get_user_status")
async def get_user_status(user_id: int):
    try:
        user_data = read_user_data()
        user_info = user_data.get(str(user_id), {
            "attempts_left": MAX_ATTEMPTS,
            "gifts": []
        })
        return user_info
    except Exception as e:
        logging.error(f"Error in get_user_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/spin")
async def spin_roulette(request: Request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="No user_id provided")
            
        user_data = read_user_data()
        user_info = user_data.get(str(user_id))
        
        if not user_info:
            raise HTTPException(status_code=404, detail="User not found")
            
        if user_info['attempts_left'] <= 0:
            raise HTTPException(status_code=400, detail="No attempts left")
            
        # Получаем выигранный приз
        won_prize = custom_methods.get_random_prize()
        
        # Обновляем данные пользователя
        user_info['attempts_left'] -= 1
        if won_prize['starPrice'] > 0:  # Если выиграл реальный приз
            won_prize['date'] = datetime.now().strftime("%d.%m.%Y %H:%M")
            user_info['gifts'].append(won_prize)
            
        save_user_data(user_data)
        
        return {
            "won_prize": won_prize,
            "attempts_left": user_info['attempts_left']
        }
    except Exception as e:
        logging.error(f"Error in spin_roulette: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/user_data")
async def get_admin_user_data(request: Request):
    """API для получения данных всех пользователей (только для админа)"""
    try:
        # Получаем данные из хедера
        telegram_data = request.headers.get('telegram-web-app-data')
        if not telegram_data:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Проверяем, что запрос от админа
        user_id = verify_telegram_web_app_data(telegram_data)
        if user_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Читаем и возвращаем данные пользователей
        all_data = read_user_data()
        return all_data
    except Exception as e:
        logging.error(f"Error in admin data access: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

# --- 6. Telegram Bot Handlers ---
@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🎲 Открыть рулетку", web_app=WebAppInfo(url=config.webapp_url))]
        ]
    )
    await message.answer(f"Привет, {message.from_user.full_name}! Нажми на кнопку ниже, чтобы открыть рулетку.", reply_markup=keyboard)

@dp.message(Command("admin"))
async def admin_command_handler(message: Message) -> None:
    """Обработчик команды /admin"""
    if message.from_user.id != config.admin_id:
        await message.answer("У вас нет прав администратора.")
        return
        
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👑 Открыть админ-панель", web_app=WebAppInfo(url=f"{config.webapp_url}/admin.html"))]
        ]
    )
    await message.answer("Панель администратора:", reply_markup=keyboard)

# --- 7. Webhook Setup ---
@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=200)
    except Exception as e:
        logging.error(f"Error in webhook handler: {e}")
        return Response(status_code=500)

# --- 8. Startup Event ---
@app.on_event("startup")
async def on_startup():
    try:
        webhook_url = f"{config.webapp_url}/webhook"
        webhook_info = await bot.get_webhook_info()
        
        # Если вебхук уже установлен на нужный URL, не меняем его
        if webhook_info.url != webhook_url:
            # Для Telegram требуется HTTPS
            if not webhook_url.startswith("https://"):
                logging.error(f"Webhook URL must start with HTTPS. Current URL: {webhook_url}")
                return
                
            await bot.delete_webhook()
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                allowed_updates=["message", "callback_query"]
            )
            logging.info(f"Webhook has been set to {webhook_url}")
        else:
            logging.info(f"Webhook is already set to {webhook_url}")
    except Exception as e:
        logging.error(f"Failed to set webhook: {e}")
        # Не прерываем запуск приложения из-за ошибки вебхука
        # Это позволит хотя бы веб-интерфейсу работать

# --- 9. Shutdown Event ---
@app.on_event("shutdown")
async def on_shutdown():
    try:
        await bot.session.close()
        logging.info("Bot session closed")
    except Exception as e:
        logging.error(f"Error during shutdown: {e}")

# --- 10. Root endpoint ---
@app.get("/")
async def root():
    return FileResponse("index.html")

# --- 11. Webhook endpoint ---
@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=200)
    except Exception as e:
        logging.error(f"Error in webhook handler: {e}")
        return Response(status_code=500) 