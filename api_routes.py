from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime
from database import get_db, Database
from models import Prize, UserPrize

router = APIRouter(prefix="/api", tags=["api"])

class SpinResult(BaseModel):
    prize_id: int
    name: str
    image_url: str
    description: str

@router.get("/prizes/{user_id}", response_model=List[Prize])
async def get_user_prizes(user_id: int, db: Database = Depends(get_db)):
    """Получение списка призов пользователя"""
    try:
        prizes = await db.get_user_prizes(user_id)
        return prizes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/spin/{user_id}", response_model=SpinResult)
async def spin_roulette(user_id: int, db: Database = Depends(get_db)):
    """Крутить рулетку и получить приз"""
    try:
        # Проверка количества попыток за день
        spins_today = await db.get_spins_count(user_id, datetime.now())
        if spins_today >= 2:
            raise HTTPException(
                status_code=400,
                detail="Превышен лимит попыток на сегодня"
            )
        
        # Получение случайного приза
        prize = await db.get_random_prize()
        if not prize:
            raise HTTPException(
                status_code=404,
                detail="Призы закончились"
            )
        
        # Сохранение результата
        await db.save_user_prize(
            UserPrize(
                user_id=user_id,
                prize_id=prize.id,
                received_at=datetime.now()
            )
        )
        
        return SpinResult(
            prize_id=prize.id,
            name=prize.name,
            image_url=prize.image_url,
            description=prize.description
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 