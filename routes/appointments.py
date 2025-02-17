"""
Маршруты для работы с заявками в системе бронирования парикмахерской.
Использует Supabase для управления заявками.
"""

import logging
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
from supabase import create_client, Client
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Инициализация клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()
security = HTTPBearer()

class Appointment(BaseModel):
    id: int
    user_id: str
    appointment_date: str
    status: str
    comments: Optional[str]
    created_at: str
    updated_at: str

class AppointmentCreate(BaseModel):
    appointment_date: str
    comments: Optional[str] = None

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    user_resp = supabase.auth.get_user(token.credentials)
    if user_resp.user is None:
        error_message = user_resp.error.message if user_resp.error else "Ошибка получения данных пользователя."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    return user_resp.user

@router.get("/appointments", response_model=List[Appointment])
async def get_appointments(user=Depends(get_current_user)):
    """
    Возвращает список всех заявок в системе.
    """
    logging.info("Получение всех заявок")
    response = supabase.from_("appointments").select("*").execute()
    logging.info(f"Ответ от Supabase: {response}")
    if not response.data:
        error_message = "Ошибка при получении заявок."
        logging.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )
    return response.data

@router.post("/appointments", response_model=Appointment)
async def create_appointment(appointment: AppointmentCreate, user=Depends(get_current_user)):
    """
    Создает новую заявку для текущего пользователя.
    """
    logging.info(f"Создание заявки для пользователя: {user.id} на дату: {appointment.appointment_date}")
    response = supabase.from_("appointments").insert({
        "user_id": user.id,
        "appointment_date": appointment.appointment_date,
        "comments": appointment.comments
    }).execute()
    logging.info(f"Ответ от Supabase: {response}")
    if not response.data:
        error_message = "Дата уже занята" if "unique constraint" in response.error.message else "Ошибка при создании заявки."
        logging.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT if "unique constraint" in response.error.message else status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )
    return response.data[0]

@router.delete("/appointments/{id}")
async def delete_appointment(id: int, user=Depends(get_current_user)):
    """
    Удаляет заявку по ID для текущего пользователя.
    """
    logging.info(f"Удаление заявки с ID: {id} для пользователя: {user.id}")
    # Проверяем, существует ли заявка и принадлежит ли она текущему пользователю
    response = supabase.from_("appointments").select("*").eq("id", id).eq("user_id", user.id).execute()
    logging.info(f"Ответ от Supabase: {response}")
    if not response.data:
        error_message = "Заявка не найдена."
        logging.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_message
        )
    
    # Удаляем заявку
    delete_response = supabase.from_("appointments").delete().eq("id", id).execute()
    logging.info(f"Ответ от Supabase при удалении: {delete_response}")
    if not delete_response.data:
        error_message = "Ошибка при удалении заявки."
        logging.error(error_message)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )
    return {"success": True, "message": "Заявка успешно отменена."} 