#!/usr/bin/env python3
"""
Backend Authentication System with FastAPI and Supabase

Это приложение реализует аутентификацию, регистрацию и управление сессиями с
использованием Supabase в качестве основного поставщика аутентификации и базы данных.
"""

from fastapi import FastAPI
from routes import auth  # Роутер с эндпоинтами аутентификации
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os

# Загрузка переменных окружения из .env
load_dotenv()

app = FastAPI(
    title="Backend Authentication System with FastAPI and Supabase",
    description="Аутентификация, регистрация и управление сессиями через Supabase.",
    version="1.0"
)

# Настройка CORS (для продакшена разрешите только доверенные домены)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер для аутентификации с префиксом /auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])


@app.get("/")
async def root():
    return {"message": "Backend Authentication System is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 