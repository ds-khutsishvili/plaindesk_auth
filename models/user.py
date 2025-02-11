#!/usr/bin/env python3
"""
В этом файле описываются модели, относящиеся к пользователю.
Содержится:
- ORM-модель User для хранения информации о пользователе в базе данных.
- Pydantic модели для валидации входящих данных при регистрации и логине.
"""

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, constr, Field

# Создаем базовый класс для ORM моделей.
Base = declarative_base()

UsernameStr = constr(min_length=3, max_length=50)
PasswordStr = constr(min_length=6, max_length=128)

# ORM-модель для хранения информации о пользователе.
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)  # Уникальное имя пользователя
    hashed_password = Column(String(255), nullable=False)  # Хранение хэшированного пароля


# Pydantic модель для регистрации нового пользователя.
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)  # Ограничения на длину имени
    password: str = Field(..., min_length=6, max_length=128)   # Ограничения на длину пароля

    class Config:
        orm_mode = True


# Pydantic модель для аутентификации (логина).
class UserLogin(BaseModel):
    username: str
    password: str


# Pydantic модель для возврата данных пользователя.
class UserResponse(BaseModel):
    id: int
    username: str

    class Config:
        orm_mode = True
