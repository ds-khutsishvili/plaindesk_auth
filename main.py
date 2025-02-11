#!/usr/bin/env python3
"""
Этот файл является точкой входа для микросервиса авторизации.
Он инициализирует приложение FastAPI, подключает роутеры и отвечает
за запуск сервиса. Сервис предназначен для деплоя на Heroku и использует
Supabase (PostgreSQL) для хранения данных, а также выдаёт JWT токены.
"""

from fastapi import FastAPI
from routes import auth  # Импортируем роутер для авторизации
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(
    title="Auth Microservice",
    description="Микросервис для регистрации и аутентификации пользователей через Supabase",
    version="2.0"
)

# Настройка CORS: разрешите нужные домены или используйте ["*"] для тестов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для продакшна рекомендуется ограничивать список доменов
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер с префиксом /auth
app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/")
async def read_root():
    return {"message": "Приложение работает как часы!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 