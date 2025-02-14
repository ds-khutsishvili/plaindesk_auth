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

class UserEmail(BaseModel):
    email: EmailStr

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
            "email_redirect_to": os.getenv("EMAIL_REDIRECT_URL", "https://YOUR_FRONTEND_URL/verify")
        }
    })
    if resp.status_code != 200 or not resp.user:
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
async def login(user: UserIn):
    """
    Аутентифицирует пользователя через Supabase и возвращает access и refresh токены.
    """
    auth_resp = supabase.auth.sign_in_with_password({
        "email": user.email,
        "password": user.password
    })
    if auth_resp.status_code != 200 or not auth_resp.session:
        err_msg = auth_resp.error.message if auth_resp.error else "Ошибка аутентификации."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err_msg
        )
    session = auth_resp.session
    return {"access_token": session.access_token, "refresh_token": session.refresh_token, "token_type": "bearer"}

# Эндпоинт: выход (logout)
@router.post("/logout")
async def logout(response: Response):
    """
    Завершает сессию пользователя через Supabase и очищает refresh token cookie.
    """
    signout_resp = supabase.auth.sign_out()
    if signout_resp.status_code != 200:
        err_msg = signout_resp.error.message if signout_resp.error else "Ошибка выхода."
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)
    response.delete_cookie("refresh_token")
    return {"message": "Вы успешно вышли из приложения."}

# Эндпоинт: обновление access token через refresh token
@router.post("/refresh", response_model=Token)
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
    if refresh_resp.status_code != 200 or not refresh_resp.session:
        err_msg = refresh_resp.error.message if refresh_resp.error else "Не удалось обновить сессию."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err_msg
        )
    session = refresh_resp.session
    return {"access_token": session.access_token, "refresh_token": session.refresh_token, "token_type": "bearer"}

# Эндпоинт: получение данных текущего пользователя через запрос getsession от Supabase.
@router.get("/users/me")
async def get_user_details(token: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """
    Возвращает данные авторизованного пользователя.
    Передается access token в заголовке Authorization в формате Bearer.
    """
    user_resp = supabase.auth.get_user(token.credentials)
    if user_resp.status_code != 200 or not user_resp.user:
        err_msg = user_resp.error.message if user_resp.error else "Ошибка получения данных пользователя."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=err_msg
        )
    return {"user": user_resp.user}

@router.post("/widgets")
async def get_widgets_by_email(user_email: UserEmail):
    """
    Возвращает виджеты, относящиеся к пользователю по email.
    """
    # Получаем пользователя по email
    user_response = supabase.from_("users").select("id").eq("email", user_email.email).execute()
    if not user_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    user_id = user_response.data[0]["id"]

    # Получаем виджеты по user_id
    widgets_response = supabase.from_("widgets").select("*").eq("user_id", user_id).execute()
    if not widgets_response.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении виджетов"
        )

    return widgets_response.data 