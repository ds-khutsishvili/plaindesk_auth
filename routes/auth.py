"""
В данном модуле описаны API эндпоинты для авторизации:
- /register — регистрация нового пользователя;
- /login — аутентификация пользователя с выдачей JWT токена.

Эндпоинты используют зависимости для подключения к базе данных и бизнес-логику, 
содержащуюся в сервисном слое, для обеспечения современных стандартов авторизации.
"""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from supabase import create_client, Client
from jose import jwt
from passlib.context import CryptContext

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

@router.post("/register", response_model=Token)
async def register(user: UserIn):
    """
    Регистрация нового пользователя через Supabase.
    """
    # Регистрация пользователя через Supabase
    response = supabase.auth.sign_up({"email": user.email, "password": user.password})
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=response.error.message
        )
    # После успешной регистрации генерируем JWT токен
    jwt_token = create_jwt_token(user.email)
    return {"access_token": jwt_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(user: UserIn):
    """
    Аутентификация пользователя через Supabase и выдача JWT токена.
    """
    response = supabase.auth.sign_in_with_password({"email": user.email, "password": user.password})
    if response.error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=response.error.message
        )
    # Если аутентификация прошла успешно – генерируем JWT токен
    jwt_token = create_jwt_token(user.email)
    return {"access_token": jwt_token, "token_type": "bearer"} 