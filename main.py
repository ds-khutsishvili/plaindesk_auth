"""
Основной файл приложения для аутентификации и регистрации пользователей в системе парикмахерской.
Использует FastAPI и Supabase для управления пользователями и сессиями.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, appointments  # Импортируем маршруты для аутентификации и заявок

app = FastAPI()

# Настройка CORS (Cross-Origin Resource Sharing)
# Позволяет вашему приложению принимать запросы с других доменов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешает запросы с любых доменов (измените на конкретные домены в продакшене)
    allow_credentials=True,
    allow_methods=["*"],  # Разрешает все HTTP методы (GET, POST, PUT, DELETE и т.д.)
    allow_headers=["*"],  # Разрешает все заголовки
)

# Подключение маршрутов
app.include_router(auth.router, prefix="/auth", tags=["auth"])  # Маршруты для аутентификации
app.include_router(appointments.router, prefix="/api", tags=["appointments"])  # Маршруты для работы с заявками

@app.get("/")
async def root():
    # Корневой эндпоинт, возвращает сообщение о работоспособности приложения
    return {"message": "Система аутентификации парикмахерской работает"} 