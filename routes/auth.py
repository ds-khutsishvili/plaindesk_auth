"""
В данном модуле описаны API эндпоинты для авторизации:
- /register — регистрация нового пользователя;
- /login — аутентификация пользователя с выдачей JWT токена.

Эндпоинты используют зависимости для подключения к базе данных и бизнес-логику, 
содержащуюся в сервисном слое, для обеспечения современных стандартов авторизации.
"""

import os
from datetime import datetime, timedelta
import logging

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr

from supabase import create_client, Client
from jose import jwt
from passlib.context import CryptContext

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")  # используйте анонимный или сервисный ключ
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Необходимо установить SUPABASE_URL и SUPABASE_KEY в переменных окружения")

# Инициализируем клиента Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Модели для запроса и ответа
class UserIn(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

# Функция для создания JWT токена
def create_jwt_token(subject: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return token

@router.post("/register")
async def register(user: UserIn):
    """
    Эндпоинт для регистрации пользователя.

    Регистрируем пользователя через Supabase и запускаем процесс подтверждения email,
    передавая параметр "email_redirect_to" внутри опций с URL-адресом подтверждения.
    """
    response = supabase.auth.sign_up({
        "email": user.email,
        "password": user.password,
        "options": {
            "email_redirect_to": "https://plaindesk-auth-d79316ebc4f2.herokuapp.com/auth/verify"
        }
    })

    # Логируем полный ответ от Supabase
    logging.info(f"Supabase response: {response}")

    # Проверяем наличие ошибки в ответе
    if response.user is None:
        error_message = response.error.message if response.error else "Ошибка регистрации: пользователь не создан."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    # Возвращаем данные пользователя, если регистрация успешна
    return {
        "message": "Регистрация успешна! Проверьте вашу почту для подтверждения email.",
        "user": response.user
    }

@router.get("/verify")
async def verify_email():
    """
    Эндпоинт для обработки редиректа после подтверждения email.
    
    После того как пользователь переходит по ссылке из письма,
    ему возвращается сообщение об успешном подтверждении email.
    """
    return {"message": "Ваш email успешно подтверждён! Теперь вы можете войти в систему."}

@router.get("/logout")
async def logout():
    """
    Эндпоинт для выхода из приложения и закрытия сессии через Supabase.
    """
    response = supabase.auth.sign_out()
    
    if response.user is None:
        error_message = response.error.message if response.error else "Ошибка при выходе из системы"
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=error_message
        )

    return {"message": "Вы успешно вышли из приложения"}

@router.post("/login", response_model=Token)
async def login(user: UserIn):
    """
    Аутентификация пользователя через Supabase и выдача JWT токена.
    """
    response = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
    response_dict = response.__dict__
    if response_dict.get("error"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response_dict["error"].message
        )
    # Получаем токен из ответа Supabase
    access_token = response_dict["session"].access_token
    return {"access_token": access_token, "token_type": "bearer"}

security = HTTPBearer()

def get_current_user(token: HTTPAuthorizationCredentials = Depends(security)):
    """
    Использует запрос getsession от Supabase для получения данных сессии/пользователя.
    """
    # Используем API-запрос Supabase для получения информации о пользователе по JWT
    user_response = supabase.auth.api.get_user(token.credentials)
    if user_response.error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=user_response.error.message
        )
    return user_response.user

@router.get("/me")
async def get_me(user = Depends(get_current_user)):
    """
    Эндпоинт для получения данных текущего пользователя.
    Реализовано с использованием запроса getsession в Supabase.
    """
    return {"user": user}