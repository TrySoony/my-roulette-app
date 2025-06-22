from aiogram.methods.base import TelegramMethod
from typing import List, Dict, Any
from pydantic import BaseModel, Field
import random


class StarAmount(BaseModel):
    star_amount: int = Field(..., alias="amount")


class Gift(BaseModel):
    id: str
    title: str
    count: int


class GiftList(BaseModel):
    gifts: List[Gift]


class GetFixedBusinessAccountStarBalance(TelegramMethod[StarAmount]):
    __returning__ = StarAmount
    __api_method__ = "getBusinessAccountStarBalance"

    business_connection_id: str


class GetFixedBusinessAccountGifts(TelegramMethod[GiftList]):
    __returning__ = GiftList
    __api_method__ = "getBusinessAccountGifts"

    business_connection_id: str

class TransferGift(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "transferGift"

    business_connection_id: str
    gift_id: str
    receiver_user_id: int

def get_random_prize() -> Dict[str, Any]:
    """Возвращает случайный приз из списка доступных призов"""
    prizes = [
        {
            "name": "Кольцо с бриллиантом",
            "img": "/images/diamond_ring.png",
            "starPrice": 5
        },
        {
            "name": "Световой меч",
            "img": "/images/light_sword.png",
            "starPrice": 4
        },
        {
            "name": "Браслет с гвоздями",
            "img": "/images/nail_bracelet.png",
            "starPrice": 3
        },
        {
            "name": "Пасхальное яйцо",
            "img": "/images/easter_egg.png",
            "starPrice": 2
        },
        {
            "name": "Шлем Неко",
            "img": "/images/neko_helmet.png",
            "starPrice": 2
        },
        {
            "name": "Кольцо верности",
            "img": "/images/bonded_ring.png",
            "starPrice": 1
        },
        {
            "name": "Любовное зелье",
            "img": "/images/love_potion.png",
            "starPrice": 1
        }
    ]
    
    # Шансы выпадения приза (в процентах)
    chances = {
        5: 5,    # 5% шанс для призов со стоимостью 5 звезд
        4: 10,   # 10% шанс для призов со стоимостью 4 звезды
        3: 15,   # 15% шанс для призов со стоимостью 3 звезды
        2: 25,   # 25% шанс для призов со стоимостью 2 звезды
        1: 45,   # 45% шанс для призов со стоимостью 1 звезда
    }
    
    # Определяем стоимость приза на основе шансов
    roll = random.randint(1, 100)
    target_price = None
    cumulative_chance = 0
    
    for price, chance in chances.items():
        cumulative_chance += chance
        if roll <= cumulative_chance:
            target_price = price
            break
    
    # Если приз не выпал, возвращаем пустой приз
    if target_price is None:
        return {"name": "Пусто", "starPrice": 0}
    
    # Выбираем случайный приз с выпавшей стоимостью
    eligible_prizes = [p for p in prizes if p["starPrice"] == target_price]
    if not eligible_prizes:
        return {"name": "Пусто", "starPrice": 0}
    
    return random.choice(eligible_prizes)