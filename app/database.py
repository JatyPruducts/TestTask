from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# Асинхронный движок
engine = create_async_engine(
    settings.get_data_base_url,
    echo=settings.DEBUG
)

# Фабрика сессий
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Класс для всех моделей
class Base(DeclarativeBase):
    pass

# Функция выдачи сессии БД
async def get_db():
    async with async_session_factory() as session:
        yield session