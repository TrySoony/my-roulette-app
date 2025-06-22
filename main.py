from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.client.default import DefaultBotProperties
import logging
import json
import os
import random
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import hmac
import hashlib
import base64
from urllib.parse import parse_qs
import time
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
bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
        logging.error("Could not read or parse user_data.json, returning empty dict.")
        return {}

def write_user_data(data):
    try:
        with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error writing user data: {e}")
        return False

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

# --- 4. FastAPI эндпоинты ---

@app.post("/webhook")
async def webhook_handler(request: Request):
    """ Эндпоинт для приема обновлений от Telegram """
    if config.webhook_secret and request.headers.get('x-telegram-bot-api-secret-token') != config.webhook_secret:
        logging.warning("Invalid secret token received")
        raise HTTPException(status_code=401, detail="Invalid secret token")
    try:
        data = await request.json()
        update = types.Update(**data)
        await dp.feed_update(bot=bot, update=update)
        return Response(status_code=200)
    except Exception as e:
        logging.error(f"Error in webhook handler: {e}")
        return Response(status_code=500)

@app.get('/api/get_user_status')
def get_user_status(user_id: str):
    """ API для получения статуса пользователя (попытки, призы) """
    if not user_id.isdigit(): raise HTTPException(400, "Invalid user_id")
    all_data = read_user_data()
    user_info = all_data.get(user_id, {"attempts": 0, "gifts": []})
    if user_id not in all_data:
        all_data[user_id] = user_info
        write_user_data(all_data)
    return {"attempts_left": MAX_ATTEMPTS - user_info.get("attempts", 0), "gifts": user_info.get("gifts", [])}

@app.post('/api/user')
async def handle_user_data(request: Request):
    """ API для инициализации пользователя в системе """
    try:
        data = await request.json()
        user_id = data.get('user_id')
        if not isinstance(user_id, int) or user_id <= 0: raise HTTPException(400, "Invalid user_id")
        all_data = read_user_data()
        if str(user_id) not in all_data:
            all_data[str(user_id)] = {"attempts": 0, "gifts": []}
            write_user_data(all_data)
        return {"status": "ok"}
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")


@app.post('/api/spin')
async def handle_spin(request: Request):
    """ API для совершения прокрутки в рулетке """
    data = await request.json()
    user_id = str(data.get('user_id'))
    if not user_id.isdigit(): raise HTTPException(400, "Invalid user_id")
    
    all_data = read_user_data()
    user_info = all_data.get(user_id, {"attempts": 0, "gifts": []})
    
    if user_info.get("attempts", 0) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=403, detail="No attempts left")
    
    user_info["attempts"] = user_info.get("attempts", 0) + 1
    
    prizes_list = [
        {"name": "Nail Bracelet", "starPrice": 100000, "img": "images/nail_bracelet.png"},
        {"name": "Bonded Ring", "starPrice": 37500, "img": "images/bonded_ring.png"},
        {"name": "Neko Helmet", "starPrice": 14000, "img": "images/neko_helmet.png"},
        {"name": "Diamond Ring", "starPrice": 6700, "img": "images/diamond_ring.png"},
        {"name": "Love Potion", "starPrice": 4200, "img": "images/love_potion.png"},
        {"name": "Easter Egg", "starPrice": 1050, "img": "images/easter_egg.png"},
        {"name": "Light Sword", "starPrice": 1450, "img": "images/light_sword.png"},
    ]
    won_prize = random.choice(prizes_list)
    
    if won_prize["starPrice"] > 0:
        gift_data = {**won_prize, "date": datetime.now().strftime('%d.%m.%Y')}
        user_info.setdefault("gifts", []).append(gift_data)

    all_data[user_id] = user_info
    write_user_data(all_data)
    
    return {"won_prize": won_prize, "attempts_left": MAX_ATTEMPTS - user_info["attempts"]}

@app.get('/api/admin/user_data')
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
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/admin/add_attempt')
async def admin_add_attempt(request: Request):
    """API для добавления попытки пользователю (только для админа)"""
    try:
        data = await request.json()
        admin_id = data.get('admin_id')
        user_id = str(data.get('user_id'))

        if not admin_id or admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")

        all_data = read_user_data()
        user_info = all_data.get(user_id, {"attempts": 0, "gifts": []})
        user_info["attempts"] = max(0, user_info.get("attempts", 0) - 1)  # Уменьшаем количество использованных попыток
        all_data[user_id] = user_info
        write_user_data(all_data)

        return {"success": True, "attempts": user_info["attempts"]}
    except Exception as e:
        logging.error(f"Error in admin add attempt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/admin/reset_attempts')
async def admin_reset_attempts(request: Request):
    """API для сброса попыток пользователя (только для админа)"""
    try:
        data = await request.json()
        admin_id = data.get('admin_id')
        user_id = str(data.get('user_id'))

        if not admin_id or admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")

        all_data = read_user_data()
        user_info = all_data.get(user_id, {"attempts": 0, "gifts": []})
        user_info["attempts"] = 0
        all_data[user_id] = user_info
        write_user_data(all_data)

        return {"success": True}
    except Exception as e:
        logging.error(f"Error in admin reset attempts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/admin/remove_gift')
async def admin_remove_gift(request: Request):
    """API для удаления приза у пользователя (только для админа)"""
    try:
        data = await request.json()
        admin_id = data.get('admin_id')
        user_id = str(data.get('user_id'))
        gift_index = data.get('gift_index')

        if not admin_id or admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")

        all_data = read_user_data()
        user_info = all_data.get(user_id)
        if not user_info or 'gifts' not in user_info:
            raise HTTPException(status_code=404, detail="User or gifts not found")

        if 0 <= gift_index < len(user_info['gifts']):
            user_info['gifts'].pop(gift_index)
            all_data[user_id] = user_info
            write_user_data(all_data)
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="Invalid gift index")
    except Exception as e:
        logging.error(f"Error in admin remove gift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/admin/add_prize')
async def admin_add_prize(request: Request):
    """API для выдачи приза пользователю (только для админа)"""
    try:
        data = await request.json()
        admin_id = data.get('admin_id')
        user_id = str(data.get('user_id'))
        prize = data.get('prize')

        if not admin_id or admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")

        if not prize or not isinstance(prize, dict):
            raise HTTPException(status_code=400, detail="Invalid prize data")

        all_data = read_user_data()
        user_info = all_data.get(user_id, {"attempts": 0, "gifts": []})
        
        # Добавляем дату к призу
        gift_data = {**prize, "date": datetime.now().strftime('%d.%m.%Y')}
        user_info.setdefault("gifts", []).append(gift_data)
        
        all_data[user_id] = user_info
        write_user_data(all_data)

        return {"success": True}
    except Exception as e:
        logging.error(f"Error in admin add prize: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- 5. Обработчики команд Aiogram ---

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обработчик команды /start"""
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="🎲 Открыть рулетку", web_app=types.WebAppInfo(url=config.webapp_url))]
        ]
    )
    await message.answer(f"Привет, {message.from_user.full_name}! Нажми на кнопку ниже, чтобы открыть рулетку.", reply_markup=keyboard)

@dp.message(lambda message: message.text == "/admin")
async def admin_command_handler(message: Message) -> None:
    """Обработчик команды /admin"""
    if message.from_user.id != config.admin_id:
        await message.answer("У вас нет прав администратора.")
        return
        
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [types.InlineKeyboardButton(text="👑 Открыть админ-панель", web_app=types.WebAppInfo(url=f"{config.webapp_url}/admin.html"))]
        ]
    )
    await message.answer("Панель администратора:", reply_markup=keyboard)

# --- 6. Раздача статических файлов ---

# ВАЖНО: эти маршруты должны быть в конце
app.mount("/images", StaticFiles(directory="images"), name="images")

@app.get("/{file_path:path}")
async def serve_static_files(file_path: str):
    # Отдаем index.html для корневого запроса
    if file_path in ["", "index.html"]:
        return FileResponse("index.html")
        
    # Белый список разрешенных файлов для безопасности
    allowed_files = ["admin.html", "style.css", "roulette.js", "prizes.js", "admin.js"]
    if file_path in allowed_files and os.path.exists(file_path):
        return FileResponse(file_path)
    
    # Если файл не найден в белом списке, возвращаем 404
    logging.warning(f"Static file not found or not allowed: {file_path}")
    raise HTTPException(status_code=404, detail="Not Found")

# --- 7. Жизненный цикл приложения ---

@app.on_event("startup")
async def on_startup():
    if config.webhook_url:
        await bot.set_webhook(
            url=f"{config.webhook_url}/webhook",
            drop_pending_updates=True,
            secret_token=config.webhook_secret
        )
        logging.info(f"Webhook has been set to {config.webhook_url}/webhook")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logging.info("Webhook has been deleted.") 