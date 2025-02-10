"""
Данный модуль отвечает за создание и проверку JWT токенов.
После успешной аутентификации создается токен, 
который позволяет защищать эндпоинты микросервиса.
Секретный ключ, алгоритм и время жизни токена загружаются из переменных окружения.
"""

import os
from datetime import datetime, timedelta
from jose import jwt, JWTError

# Чтение настроек из переменных окружения с указанием значений по умолчанию.
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


def create_access_token(data: dict) -> str:
    """
    Создает JWT токен.
    Добавляет время окончания действия токена (exp) и кодирует данные.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict:
    """
    Декодирует и проверяет JWT токен.
    При ошибке декодирования выбрасывает исключение JWTError.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise e 