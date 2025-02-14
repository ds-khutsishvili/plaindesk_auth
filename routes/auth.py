"""
В данном модуле реализованы API-эндпоинты для авторизации:
- POST /register   — регистрация нового пользователя;
- POST /login      — аутентификация и выдача JWT (access token), хранение refresh token в HttpOnly cookie;
- POST /logout     — завершение сессии и удаление refresh token;
- POST /refresh    — обновление access token с использованием refresh token;
- GET /users/me    — получение данных авторизованного пользователя через Supabase.
"""

import os
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # Анонимный или сервисный ключ
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
# Остальные JWT настройки можно использовать, если потребуется создавать свои токены

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Необходимо установить SUPABASE_URL и SUPABASE_KEY в переменных окружения")

# Инициализация клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

# Модели запросов и ответов
class UserIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# PATCH: Можно добавить дополнительные модели для refresh, logout и т.д.

# Эндпоинт: регистрация нового пользователя
@router.post("/register")
async def register(user: UserIn):
    """
    Регистрирует пользователя через Supabase и отправляет письмо для подтверждения email.
    """
    resp = supabase.auth.sign_up({
        "email": user.email,
        "password": user.password,
        "options": {
            "email_redirect_to": os.getenv("EMAIL_REDIRECT_URL", "https://YOUR_FRONTEND_URL/verify")  # Используем переменную окружения
        }
    })
    # Логируем ответ для отладки
    logging.info(f"Supabase sign up response: {resp}")

    if resp.user is None:
        err_msg = resp.error.message if resp.error else "Ошибка регистрации: пользователь не создан."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg
        )
    return {
        "message": "Регистрация успешна! Проверьте свою почту для подтверждения email.",
        "user": resp.user
    }

# Эндпоинт: аутентификация (логин)
@router.post("/login", response_model=Token)
async def login(user: UserIn, response: Response):
    """
    Аутентифицирует пользователя через Supabase и возвращает access token.
    refresh token устанавливается в HttpOnly cookie.
    """
    auth_resp = supabase.auth.sign_in_with_password({
        "email": user.email,
        "password": user.password
    })
    auth_dict = auth_resp.__dict__
    if auth_dict.get("error"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=auth_dict["error"].message
        )
    session = auth_dict.get("session")
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия не создана."
        )
    access_token = session.access_token
    refresh_token = session.refresh_token
    # Сохраняем refresh token в HttpOnly cookie
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, secure=True)
    return {"access_token": access_token, "token_type": "bearer"}

# Эндпоинт: выход (logout)
@router.post("/logout")
async def logout(response: Response):
    """
    Завершает сессию пользователя через Supabase и очищает refresh token cookie.
    """
    signout_resp = supabase.auth.sign_out()
    signout_dict = signout_resp.__dict__
    if signout_dict.get("error"):
        err_msg = signout_dict["error"].message
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    # Очистка refresh token cookie
    response.delete_cookie("refresh_token")
    return {"message": "Вы успешно вышли из приложения."}

# Эндпоинт: обновление access token через refresh token
@router.post("/refresh", response_model=Token)
async def refresh_token(request: Request, response: Response):
    """
    Обновляет access token, используя refresh token, который хранится в HttpOnly cookie.
    """
    refresh_token_val = request.cookies.get("refresh_token")
    if not refresh_token_val:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token отсутствует."
        )
    refresh_resp = supabase.auth.refresh_session({"refresh_token": refresh_token_val})
    refresh_dict = refresh_resp.__dict__
    if refresh_dict.get("error"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=refresh_dict["error"].message
        )
    session = refresh_dict.get("session")
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось обновить сессию."
        )
    new_access_token = session.access_token
    new_refresh_token = session.refresh_token
    # Обновляем refresh token в cookie
    response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, secure=True)
    return {"access_token": new_access_token, "token_type": "bearer"}

# Эндпоинт: получение данных текущего пользователя через запрос getsession от Supabase.
@router.get("/users/me")
async def get_user_details(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    Возвращает данные авторизованного пользователя.
    Передается access token в заголовке Authorization в формате Bearer.
    """
    user_resp = supabase.auth.api.get_user(token.credentials)
    if user_resp.error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=user_resp.error.message
        )
    return {"user": user_resp.user} 