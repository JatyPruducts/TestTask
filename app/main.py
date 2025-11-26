from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.routers import router


# Логика запуска и остановки
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# Инициализация приложения
app = FastAPI(
    title="Lead Distribution Service",
    description="Мини-CRM для распределения заявок между операторами с учетом весов и лимитов.",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Service is running. Documentation available at /docs"
    }
