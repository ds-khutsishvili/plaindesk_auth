"""
Этот файл отвечает за настройку подключения к базе данных.
Он создает асинхронный движок SQLAlchemy для подключения к PostgreSQL (Supabase)
с использованием драйвера asyncpg. URL подключения берется из переменных окружения.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

# Создаем базовый класс для всех ORM моделей.
Base = declarative_base()

# Получаем URL базы данных из переменных окружения.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")

# Инициализируем асинхронный движок для работы с БД.
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Создаем фабрику сессий для асинхронных операций.
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """
    Функция-генератор для получения сессии базы данных.
    Используется в качестве зависимости (Depends) в FastAPI.
    """
    async with async_session() as session:
        yield session 