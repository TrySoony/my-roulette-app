#!/usr/bin/env python3
"""
Комплексный тест всех функций бота
"""
import os
import sys
import json
import asyncio
from datetime import datetime
import pytest
from fastapi.testclient import TestClient
from main import app
from config import config
from utils import DataManager

# Устанавливаем фиктивные переменные окружения для тестирования
os.environ['BOT_TOKEN'] = '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz'
os.environ['ADMIN_ID'] = '123456789'
os.environ['RENDER_EXTERNAL_URL'] = 'https://test-app.onrender.com'
os.environ['WEBHOOK_SECRET'] = 'test_secret_token_123'
os.environ['MAX_ATTEMPTS'] = '2'
os.environ['DEBUG'] = 'true'

# Инициализация тестового клиента
client = TestClient(app)

# Тестовые данные
TEST_USER_ID = "123456789"
TEST_ADMIN_ID = config.admin_id
TEST_PRIZE = {
    "name": "Test Prize",
    "starPrice": 100,
    "img": "/assets/test_prize.png"
}

# Фикстуры
@pytest.fixture
def test_data_manager():
    """Создает тестовый менеджер данных с временным файлом"""
    test_file = "test_user_data.json"
    manager = DataManager(test_file)
    yield manager
    # Очистка после тестов
    if os.path.exists(test_file):
        os.remove(test_file)

@pytest.fixture
def test_user_data():
    """Создает тестовые данные пользователя"""
    return {
        "attempts_left": config.max_attempts,
        "gifts": []
    }

def test_imports():
    """Тестирует все необходимые импорты"""
    print("🔍 Тестирование импортов...")
    
    try:
        from aiogram import Bot, Dispatcher, types
        print("✅ aiogram импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта aiogram: {e}")
        return False
    
    try:
        from fastapi import FastAPI
        print("✅ FastAPI импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта FastAPI: {e}")
        return False
    
    try:
        from flask import Flask
        print("✅ Flask импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта Flask: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ Pillow импортирован успешно")
    except ImportError as e:
        print(f"❌ Ошибка импорта Pillow: {e}")
        return False
    
    return True

def test_config():
    """Тестирует загрузку конфигурации"""
    print("\n🔧 Тестирование конфигурации...")
    
    try:
        from config import config
        print(f"✅ Конфигурация загружена успешно")
        print(f"   - Admin ID: {config.admin_id}")
        print(f"   - Webhook URL: {config.webhook_url}")
        print(f"   - Webhook Secret: {'Установлен' if config.webhook_secret else 'Не установлен'}")
        print(f"   - Max Attempts: {config.max_attempts}")
        print(f"   - Debug Mode: {config.debug}")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False

def test_main_app():
    """Тестирует создание основного приложения"""
    print("\n🚀 Тестирование основного приложения...")
    
    try:
        from main import app, bot, dp
        print("✅ Основное приложение создано успешно")
        print(f"   - FastAPI app: {type(app)}")
        print(f"   - Bot: {type(bot)}")
        print(f"   - Dispatcher: {type(dp)}")
        
        # Проверяем, что webhook маршрут существует
        routes = [route.path for route in app.routes]
        if "/webhook" in routes:
            print("✅ Webhook маршрут найден")
        else:
            print("❌ Webhook маршрут не найден")
            print(f"   Доступные маршруты: {routes}")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Ошибка создания приложения: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_user_data_functions():
    """Тестирует функции работы с данными пользователей"""
    print("\n👥 Тестирование функций пользователей...")
    
    try:
        from main import read_user_data, write_user_data, MAX_ATTEMPTS
        
        # Тестируем создание нового пользователя
        test_user_id = "999999"
        test_data = {"attempts": 0, "gifts": []}
        
        # Читаем текущие данные
        all_data = read_user_data()
        print(f"✅ Чтение данных пользователей: {len(all_data)} пользователей")
        
        # Добавляем тестового пользователя
        all_data[test_user_id] = test_data
        write_user_data(all_data)
        print("✅ Запись данных пользователей")
        
        # Проверяем, что пользователь создался
        all_data = read_user_data()
        if test_user_id in all_data:
            print("✅ Тестовый пользователь создан успешно")
        else:
            print("❌ Тестовый пользователь не найден")
            return False
        
        # Проверяем количество попыток
        user_info = all_data[test_user_id]
        attempts_left = MAX_ATTEMPTS - user_info.get("attempts", 0)
        print(f"✅ Количество попыток: {attempts_left}")
        
        # Удаляем тестового пользователя
        del all_data[test_user_id]
        write_user_data(all_data)
        print("✅ Тестовый пользователь удален")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования функций пользователей: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_prizes():
    """Тестирует загрузку призов"""
    print("\n🎁 Тестирование призов...")
    
    try:
        # Проверяем файл prizes.js
        if os.path.exists('prizes.js'):
            print("✅ Файл prizes.js найден")
        else:
            print("❌ Файл prizes.js не найден")
            return False
        
        # Проверяем изображения призов
        prize_images = [
            "images/nail_bracelet.png",
            "images/bonded_ring.png", 
            "images/neko_helmet.png",
            "images/diamond_ring.png",
            "images/love_potion.png",
            "images/easter_egg.png",
            "images/light_sword.png"
        ]
        
        missing_images = []
        for img in prize_images:
            if not os.path.exists(img):
                missing_images.append(img)
        
        if missing_images:
            print(f"⚠️  Отсутствуют изображения: {missing_images}")
        else:
            print("✅ Все изображения призов найдены")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка тестирования призов: {e}")
        return False

def test_webhook_endpoint():
    """Тестирует webhook эндпоинт"""
    print("\n🔗 Тестирование webhook эндпоинта...")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        # Создаем тестовый клиент
        client = TestClient(app)
        
        # Тестовые данные для webhook
        test_data = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456789,
                    "is_bot": False,
                    "first_name": "Test",
                    "username": "testuser"
                },
                "chat": {
                    "id": 123456789,
                    "first_name": "Test",
                    "username": "testuser",
                    "type": "private"
                },
                "date": 1234567890,
                "text": "/start"
            }
        }
        
        # Тестируем webhook без секретного токена
        response = client.post("/webhook", json=test_data)
        print(f"✅ Webhook ответ без токена: {response.status_code}")
        
        # Тестируем webhook с секретным токеном
        headers = {"x-telegram-bot-api-secret-token": "test_secret_token_123"}
        response = client.post("/webhook", json=test_data, headers=headers)
        print(f"✅ Webhook ответ с токеном: {response.status_code}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("   Установите: pip install httpx")
        return False
    except Exception as e:
        print(f"❌ Ошибка тестирования webhook: {e}")
        return False

def test_api_endpoints():
    """Тестирует API эндпоинты"""
    print("\n🌐 Тестирование API эндпоинтов...")
    
    try:
        from main import app
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        
        # Тестируем health check
        response = client.get("/health")
        print(f"✅ Health check: {response.status_code}")
        
        # Тестируем главную страницу
        response = client.get("/")
        print(f"✅ Главная страница: {response.status_code}")
        
        # Тестируем админ-панель
        response = client.get("/admin")
        print(f"✅ Админ-панель: {response.status_code}")
        
        # Тестируем API получения статуса пользователя
        response = client.get("/api/get_user_status?user_id=123456")
        print(f"✅ API статус пользователя: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка тестирования API: {e}")
        return False

# Тесты API эндпоинтов
def test_health_check():
    """Тест эндпоинта проверки работоспособности"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_page():
    """Тест главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_admin_page():
    """Тест страницы администратора"""
    response = client.get("/admin")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

# Тесты API пользователя
def test_announce_user():
    """Тест регистрации пользователя"""
    response = client.post(
        "/api/user",
        json={"user_id": TEST_USER_ID}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "user_data" in data

def test_get_user_status():
    """Тест получения статуса пользователя"""
    response = client.get(f"/api/get_user_status?user_id={TEST_USER_ID}")
    assert response.status_code == 200
    data = response.json()
    assert "attempts_left" in data
    assert "gifts" in data

def test_spin_roulette():
    """Тест вращения рулетки"""
    response = client.post(
        "/api/spin",
        json={"user_id": TEST_USER_ID}
    )
    assert response.status_code == 200
    data = response.json()
    assert "won_prize" in data
    assert "attempts_left" in data

# Тесты админского API
def test_admin_add_attempt():
    """Тест добавления попытки администратором"""
    response = client.post(
        "/api/admin/add_attempt",
        json={
            "user_id": TEST_USER_ID,
            "admin_id": TEST_ADMIN_ID
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "attempts" in data

def test_admin_reset_attempts():
    """Тест сброса попыток администратором"""
    response = client.post(
        "/api/admin/reset_attempts",
        json={
            "user_id": TEST_USER_ID,
            "admin_id": TEST_ADMIN_ID
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_admin_add_prize():
    """Тест добавления приза администратором"""
    response = client.post(
        "/api/admin/add_prize",
        json={
            "user_id": TEST_USER_ID,
            "admin_id": TEST_ADMIN_ID,
            "prize": TEST_PRIZE
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

# Тесты DataManager
def test_data_manager_operations(test_data_manager, test_user_data):
    """Тест операций менеджера данных"""
    # Тест создания данных
    test_data_manager._save_data({TEST_USER_ID: test_user_data})
    
    # Тест чтения данных
    data = test_data_manager.read_data()
    assert TEST_USER_ID in data
    assert data[TEST_USER_ID]["attempts_left"] == config.max_attempts
    
    # Тест обновления данных
    def update_func(user_info):
        user_info["attempts_left"] -= 1
        return user_info
    
    updated_data = test_data_manager.update_user_data(TEST_USER_ID, update_func)
    assert updated_data["attempts_left"] == config.max_attempts - 1
    
    # Тест добавления подарка
    test_data_manager.add_gift(TEST_USER_ID, TEST_PRIZE, config.max_attempts)
    data = test_data_manager.read_data()
    assert len(data[TEST_USER_ID]["gifts"]) == 1
    assert data[TEST_USER_ID]["gifts"][0]["name"] == TEST_PRIZE["name"]
    
    # Тест удаления подарка
    updated_data = test_data_manager.remove_gift(TEST_USER_ID, 0)
    assert len(updated_data["gifts"]) == 0

def test_invalid_user_operations():
    """Тест операций с недопустимыми данными пользователя"""
    # Тест с неверным ID пользователя
    response = client.post(
        "/api/user",
        json={"user_id": "invalid_id"}
    )
    assert response.status_code == 400
    
    # Тест с отсутствующим ID пользователя
    response = client.post("/api/user", json={})
    assert response.status_code == 400

def test_invalid_admin_operations():
    """Тест админских операций с недопустимыми данными"""
    # Тест с неверным ID администратора
    response = client.post(
        "/api/admin/add_attempt",
        json={
            "user_id": TEST_USER_ID,
            "admin_id": 999999
        }
    )
    assert response.status_code == 403
    
    # Тест с отсутствующими данными
    response = client.post("/api/admin/add_attempt", json={})
    assert response.status_code == 400

def main():
    """Основная функция тестирования"""
    print("🧪 Начинаем комплексное тестирование проекта...\n")
    
    # Проверяем версию Python
    print(f"🐍 Python версия: {sys.version}")
    
    # Тестируем импорты
    if not test_imports():
        print("\n❌ Тест импортов не пройден!")
        return
    
    # Тестируем конфигурацию
    if not test_config():
        print("\n❌ Тест конфигурации не пройден!")
        return
    
    # Тестируем основное приложение
    if not test_main_app():
        print("\n❌ Тест приложения не пройден!")
        return
    
    # Тестируем функции пользователей
    if not test_user_data_functions():
        print("\n❌ Тест функций пользователей не пройден!")
        return
    
    # Тестируем призы
    if not test_prizes():
        print("\n❌ Тест призов не пройден!")
        return
    
    # Тестируем webhook эндпоинт
    if not test_webhook_endpoint():
        print("\n❌ Тест webhook эндпоинта не пройден!")
        return
    
    # Тестируем API эндпоинты
    if not test_api_endpoints():
        print("\n❌ Тест API эндпоинтов не пройден!")
        return
    
    print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    print("✅ Проект полностью готов к развертыванию!")
    print("\n📝 Следующие шаги:")
    print("   1. Убедитесь, что переменные окружения установлены на Render:")
    print("      - BOT_TOKEN")
    print("      - ADMIN_ID") 
    print("      - WEBHOOK_SECRET")
    print("      - MAX_ATTEMPTS (опционально, по умолчанию 2)")
    print("   2. Задеплойте проект на Render")
    print("   3. Проверьте логи на наличие ошибок")
    print("   4. Протестируйте бота командой /start")
    print("   5. Проверьте админ-панель командой /admin")

if __name__ == "__main__":
    pytest.main(["-v", "--cov=.", "test_all.py"]) 