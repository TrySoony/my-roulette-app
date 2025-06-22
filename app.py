# Импортируем FastAPI приложение из main.py
from main import app

# Экспортируем приложение для Gunicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 