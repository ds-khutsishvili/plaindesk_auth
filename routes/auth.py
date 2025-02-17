"""
Маршруты для регистрации и аутентификации пользователей.
Использует Supabase для управления пользователями и сессиями.
"""

from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client
import os

# Загрузка переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Инициализация клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

class UserIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(user: UserIn):
    """
    Регистрация нового пользователя через Supabase Auth.
    """
    response = supabase.auth.sign_up({
        "email": user.email,
        "password": user.password
    })
    if response.user is None:
        error_message = response.error.message if response.error else "Ошибка регистрации: пользователь не создан."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    return {
        "success": True,
        "message": "Регистрация успешна! Проверьте свою почту для подтверждения email.",
        "user": response.user
    }

@router.post("/login")
async def login(user: UserIn):
    """
    Аутентификация пользователя и выдача access и refresh токенов через Supabase.
    """
    response = supabase.auth.sign_in_with_password({
        "email": user.email,
        "password": user.password
    })
    if response.session is None:
        error_message = response.error.message if response.error else "Ошибка аутентификации."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    session = response.session
    return {
        "access_token": session.access_token,
        "refresh_token": session.refresh_token,
        "user": response.user
    }

@router.post("/refresh")
async def refresh_token(request: Request):
    """
    Обновляет access token, используя refresh token, который передается в теле запроса.
    """
    body = await request.json()
    refresh_token_val = body.get("refresh_token")
    if not refresh_token_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token отсутствует."
        )
    refresh_resp = supabase.auth.refresh_session({"refresh_token": refresh_token_val})
    if refresh_resp.session is None:
        error_message = refresh_resp.error.message if refresh_resp.error else "Не удалось обновить сессию."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_message
        )
    session = refresh_resp.session
    return {"access_token": session.access_token} 