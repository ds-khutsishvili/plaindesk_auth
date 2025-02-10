"""
В данном модуле описаны API эндпоинты для авторизации:
- /register — регистрация нового пользователя;
- /login — аутентификация пользователя с выдачей JWT токена.

Эндпоинты используют зависимости для подключения к базе данных и бизнес-логику, 
содержащуюся в сервисном слое, для обеспечения современных стандартов авторизации.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import UserCreate, UserLogin, UserResponse
from db.database import get_db
from services.auth_service import create_user, authenticate_user, get_user_by_username
from auth.jwt_handler import create_access_token

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Эндпоинт для регистрации нового пользователя.
    1. Проверяет, существует ли пользователь с таким именем.
    2. Если пользователь существует, возвращает ошибку 400.
    3. Если нет, хеширует пароль и создает нового пользователя.
    4. Возвращает данные созданного пользователя без пароля.
    """
    existing_user = await get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким именем уже существует."
        )
    new_user = await create_user(db, user)
    return new_user


@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Эндпоинт для аутентификации пользователя.
    1. Принимает логин и пароль.
    2. Проверяет наличие пользователя и корректность пароля.
    3. Если аутентификация проходит успешно, создает JWT токен и возвращает его.
    4. Если аутентификация неудачна, возвращает ошибку 401.
    """
    authenticated_user = await authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные учетные данные."
        )
    # Создаем JWT токен, передавая идентификатор пользователя в поле "sub".
    access_token = create_access_token(data={"sub": str(authenticated_user.id)})
    return {"access_token": access_token, "token_type": "bearer"} 