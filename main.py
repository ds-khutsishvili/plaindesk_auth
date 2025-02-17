"""
Основной файл приложения для аутентификации и регистрации пользователей в системе парикмахерской.
Использует FastAPI и Supabase для управления пользователями и сессиями.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, appointments  # Импортируем новый роутер

app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Измените на конкретные домены в продакшене
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(appointments.router, prefix="/api", tags=["appointments"])  # Подключаем роутер для заявок

@app.get("/")
async def root():
    return {"message": "Система аутентификации парикмахерской работает"} 