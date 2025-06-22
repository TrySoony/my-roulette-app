from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import logging
from config import config
from utils import DataManager

router = APIRouter(prefix="/api/admin")

# Константы
USER_DATA_FILE = "user_data.json"
MAX_ATTEMPTS = config.max_attempts

# Инициализация менеджера данных
data_manager = DataManager(USER_DATA_FILE)

@router.get("/user_data")
async def get_admin_user_data(request: Request):
    """API для получения данных всех пользователей (только для админа)"""
    try:
        # Получаем данные из хедера
        telegram_data = request.headers.get('telegram-web-app-data')
        if not telegram_data:
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Проверяем, что запрос от админа
        from api_routes import verify_telegram_web_app_data
        user_id = verify_telegram_web_app_data(telegram_data)
        if user_id != config.admin_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Читаем и возвращаем данные пользователей
        all_data = data_manager.read_data()
        return all_data
    except Exception as e:
        logging.error(f"Error in admin data access: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")

@router.post("/add_attempt")
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

@router.post("/reset_attempts")
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

@router.post("/remove_gift")
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

@router.post("/add_prize")
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