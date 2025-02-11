import os
import requests
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

# Инициализируем средство для получения токена из заголовка Authorization
security = HTTPBearer()

# URL для получения публичных ключей Supabase (JWKS)
SUPABASE_JWKS_URL = os.getenv(
    "SUPABASE_JWKS_URL",
    "https://velvccfiehxnmwscqaxc.supabase.co/auth/v1/certs"
)

def fetch_jwks():
    """
    Получает JWKS (JSON Web Key Set) с сервера Supabase.
    """
    try:
        response = requests.get(SUPABASE_JWKS_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка при получении JWKS ключей с Supabase"
        )

def verify_supabase_jwt(token: str) -> dict:
    """
    Проверяет и декодирует JWT токен с использованием публичного ключа Supabase.
    Если проверка не проходит, генерирует HTTP 401.
    """
    jwks = fetch_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный заголовок JWT"
        )
    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Отсутствует 'kid' в заголовке токена"
        )
    public_key = None
    # Ищем публичный ключ с соответствующим kid
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            public_key = key
            break
    if public_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Публичный ключ для проверки токена не найден"
        )
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный или просроченный токен"
        )

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Зависимость для получения текущего пользователя.
    Извлекает токен из заголовка Authorization, проверяет его и возвращает payload.
    """
    token = credentials.credentials
    payload = verify_supabase_jwt(token)
    return payload 