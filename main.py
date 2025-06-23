from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
from config import config

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if config.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(
    title="Prize Roulette Web App",
    description="Веб-приложение для розыгрыша призов",
    version="1.0.0",
    debug=config.debug
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    """Главная страница с рулеткой"""
    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return Response(
            content="Internal Server Error",
            status_code=500
        )

@app.get("/admin")
async def admin_panel(request: Request):
    """Админ-панель"""
    try:
        return templates.TemplateResponse(
            "admin.html",
            {"request": request}
        )
    except Exception as e:
        logger.error(f"Error rendering admin page: {e}")
        return Response(
            content="Internal Server Error",
            status_code=500
        )

@app.get("/health")
async def health_check():
    """Эндпоинт для проверки работоспособности сервиса"""
    return {"status": "healthy"}

# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=config.debug
    ) 