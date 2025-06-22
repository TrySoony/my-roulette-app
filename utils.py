import json
import os
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
from datetime import datetime

class DataManager:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Убеждаемся, что файл существует и создаем его если нет"""
        if not os.path.exists(self.file_path):
            self._save_data({})
    
    def _save_data(self, data: Dict[str, Any]) -> None:
        """Сохраняет данные в файл с обработкой ошибок"""
        try:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Error saving data to {self.file_path}: {e}")
            raise HTTPException(status_code=500, detail="Failed to save data")

    def read_data(self) -> Dict[str, Any]:
        """Читает данные из файла с обработкой ошибок"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return json.loads(content) if content else {}
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logging.error(f"Error reading data from {self.file_path}: {e}")
            return {}
        except Exception as e:
            logging.error(f"Unexpected error reading {self.file_path}: {e}")
            raise HTTPException(status_code=500, detail="Failed to read data")

    def get_user_data(self, user_id: str, max_attempts: int) -> Dict[str, Any]:
        """Получает данные пользователя, создавая новую запись если нужно"""
        data = self.read_data()
        if user_id not in data:
            data[user_id] = {
                "attempts_left": max_attempts,
                "gifts": []
            }
            self._save_data(data)
        return data[user_id]

    def update_user_data(self, user_id: str, update_func) -> Dict[str, Any]:
        """Обновляет данные пользователя используя переданную функцию"""
        data = self.read_data()
        if user_id in data:
            data[user_id] = update_func(data[user_id])
            self._save_data(data)
        return data.get(user_id, {})

    def add_gift(self, user_id: str, gift: Dict[str, Any], max_attempts: int) -> None:
        """Добавляет подарок пользователю"""
        data = self.read_data()
        if user_id not in data:
            data[user_id] = {"attempts_left": max_attempts, "gifts": []}
        
        gift['date'] = datetime.now().strftime("%d.%m.%Y %H:%M")
        data[user_id]["gifts"].append(gift)
        self._save_data(data)

    def remove_gift(self, user_id: str, gift_index: int) -> Optional[Dict[str, Any]]:
        """Удаляет подарок у пользователя"""
        data = self.read_data()
        if user_id not in data or not data[user_id].get("gifts"):
            return None
            
        if gift_index < 0 or gift_index >= len(data[user_id]["gifts"]):
            return None
            
        data[user_id]["gifts"].pop(gift_index)
        self._save_data(data)
        return data[user_id] 