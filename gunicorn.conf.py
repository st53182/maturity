# Конфиг Gunicorn для PaaS (Render, Railway и т.д.).
# Обязательно: bind на 0.0.0.0 и порт из переменной PORT — иначе платформа не достучится до процесса.
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Flask-SocketIO с async_mode='threading' в app.py — worker eventlet не подходит.
workers = 1
worker_class = "sync"
timeout = 180
