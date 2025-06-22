from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import logging
import json
import os
from config import config
import custom_methods
from urllib.parse import parse_qs
import hmac
import hashlib
from utils import DataManager

router = APIRouter(prefix="/api")

# Константы
USER_DATA_FILE = "user_data.json"
MAX_ATTEMPTS = config.max_attempts

# Инициализация менеджера данных
data_manager = DataManager(USER_DATA_FILE)

def verify_telegram_web_app_data(init_data: str) -> int:
    """Проверяет данные от Telegram Web App"""
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

@router.post("/user")
async def announce_user(request: Request):
    """Регистрирует нового пользователя в системе"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="No user_id provided")
        
        user_data = data_manager.get_user_data(str(user_id), MAX_ATTEMPTS)
        return {"status": "success", "user_data": user_data}
    except Exception as e:
        logging.error(f"Error in announce_user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_user_status")
async def get_user_status(user_id: int):
    """Получает статус пользователя"""
    try:
        user_data = data_manager.get_user_data(str(user_id), MAX_ATTEMPTS)
        return JSONResponse(content=user_data)
    except Exception as e:
        logging.error(f"Error in get_user_status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/spin")
async def spin_roulette(request: Request):
    """Обрабатывает запрос на вращение рулетки"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            raise HTTPException(status_code=400, detail="No user_id provided")
            
        user_data = data_manager.get_user_data(str(user_id), MAX_ATTEMPTS)
        
        if user_data['attempts_left'] <= 0:
            raise HTTPException(status_code=400, detail="No attempts left")
            
        # Получаем выигранный приз
        won_prize = custom_methods.get_random_prize()
        
        # Обновляем данные пользователя
        def update_user(user_info):
            user_info['attempts_left'] -= 1
            if won_prize['starPrice'] > 0:  # Если выиграл реальный приз
                won_prize['date'] = datetime.now().strftime("%d.%m.%Y %H:%M")
                user_info['gifts'].append(won_prize)
            return user_info
        
        updated_user_data = data_manager.update_user_data(str(user_id), update_user)
        
        return {
            "won_prize": won_prize,
            "attempts_left": updated_user_data['attempts_left']
        }
    except Exception as e:
        logging.error(f"Error in spin_roulette: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/add_attempt")
async def add_attempt(request: Request):
    """API для добавления попытки пользователю (только для админа)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        admin_id = data.get('admin_id')
        
        if not user_id or not admin_id:
            raise HTTPException(status_code=400, detail="Missing user_id or admin_id")
            
        if admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        def update_user(user_info):
            user_info['attempts_left'] += 1
            return user_info
            
        updated_user_data = data_manager.update_user_data(str(user_id), update_user)
        return {"success": True, "attempts": updated_user_data['attempts_left']}
    except Exception as e:
        logging.error(f"Error in add_attempt: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/reset_attempts")
async def reset_attempts(request: Request):
    """API для сброса попыток пользователя (только для админа)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        admin_id = data.get('admin_id')
        
        if not user_id or not admin_id:
            raise HTTPException(status_code=400, detail="Missing user_id or admin_id")
            
        if admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        def update_user(user_info):
            user_info['attempts_left'] = MAX_ATTEMPTS
            return user_info
            
        data_manager.update_user_data(str(user_id), update_user)
        return {"success": True}
    except Exception as e:
        logging.error(f"Error in reset_attempts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/remove_gift")
async def remove_gift(request: Request):
    """API для удаления приза у пользователя (только для админа)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        gift_index = data.get('gift_index')
        admin_id = data.get('admin_id')
        
        if not user_id or gift_index is None or not admin_id:
            raise HTTPException(status_code=400, detail="Missing user_id, gift_index or admin_id")
            
        if admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        updated_user_data = data_manager.remove_gift(str(user_id), gift_index)
        if not updated_user_data:
            raise HTTPException(status_code=404, detail="User or gift not found")
            
        return {"success": True}
    except Exception as e:
        logging.error(f"Error in remove_gift: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/admin/add_prize")
async def add_prize(request: Request):
    """API для добавления приза пользователю (только для админа)"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        prize = data.get('prize')
        admin_id = data.get('admin_id')
        
        if not user_id or not prize or not admin_id:
            raise HTTPException(status_code=400, detail="Missing user_id, prize or admin_id")
            
        if admin_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")
            
        if not isinstance(prize, dict) or not all(k in prize for k in ['name', 'starPrice', 'img']):
            raise HTTPException(status_code=400, detail="Invalid prize format")
            
        data_manager.add_gift(str(user_id), prize, MAX_ATTEMPTS)
        return {"success": True}
    except Exception as e:
        logging.error(f"Error in add_prize: {e}")
        raise HTTPException(status_code=500, detail=str(e))