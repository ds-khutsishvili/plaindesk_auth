"""
Этот файл содержит бизнес-логику для аутентификации пользователей.
Реализованы функции для хеширования пароля, проверки пароля,
поиска пользователя, создания нового пользователя и аутентификации.
"""

from passlib.context import CryptContext
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, UserCreate

# Инициализируем контекст для хеширования с использованием алгоритма bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt и возвращает хэшированное значение.
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сравнивает введенный пароль с хэшированным.
    Возвращает True, если они совпадают, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)

async def get_user_by_username(db: AsyncSession, username: str):
    """
    Ищет пользователя в базе данных по имени.
    Возвращает объект User если найден, иначе None.
    """
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    """
    Создает нового пользователя:
    1. Хеширует пароль.
    2. Создает объект пользователя.
    3. Сохраняет его в базе данных.
    Возвращает созданного пользователя.
    """
    hashed = hash_password(user.password)
    db_user = User(username=user.username, hashed_password=hashed)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    """
    Проверяет учетные данные пользователя:
    1. Получает пользователя по имени.
    2. Сравнивает введенный пароль с хэшированным.
    Возвращает объект пользователя при успешной аутентификации, иначе None.
    """
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user 