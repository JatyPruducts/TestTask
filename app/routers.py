from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas, services
from app.database import get_db

router = APIRouter()


# Управление операторами
@router.post("/operators", response_model=schemas.OperatorRead, status_code=status.HTTP_201_CREATED)
async def create_operator(
        operator_data: schemas.OperatorCreate,
        db: AsyncSession = Depends(get_db)
):
    new_operator = models.Operator(**operator_data.model_dump())
    db.add(new_operator)
    await db.commit()
    await db.refresh(new_operator)
    return new_operator


@router.get("/operators", response_model=List[schemas.OperatorRead])
async def get_operators(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Operator))
    return result.scalars().all()


# Управление источниками
@router.post("/sources", response_model=schemas.SourceRead, status_code=status.HTTP_201_CREATED)
async def create_source(
        source_data: schemas.SourceCreate,
        db: AsyncSession = Depends(get_db)
):
    existing = await db.execute(select(models.Source).where(models.Source.name == source_data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Source with this name already exists")
    new_source = models.Source(**source_data.model_dump())
    db.add(new_source)
    await db.commit()
    await db.refresh(new_source)
    return new_source


@router.get("/sources", response_model=List[schemas.SourceRead])
async def get_sources(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Source))
    return result.scalars().all()


# Настройка распределения

@router.post("/sources/{source_id}/config")
async def update_source_config(
        source_id: int,
        config: schemas.SourceConfigUpdate,
        db: AsyncSession = Depends(get_db)
):
    return await services.update_source_config_logic(db, source_id, config)


# Обработка обращений
@router.post("/inquiries", response_model=schemas.InquiryRead, status_code=status.HTTP_201_CREATED)
async def register_inquiry(
        inquiry_data: schemas.InquiryCreate,
        db: AsyncSession = Depends(get_db)
):
    return await services.create_inquiry_logic(db, inquiry_data)


# Просмотр статистики (для отладки)
@router.get("/inquiries", response_model=List[schemas.InquiryRead])
async def get_inquiries_list(limit: int = 100, db: AsyncSession = Depends(get_db)):
    stmt = select(models.Inquiry).order_by(models.Inquiry.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
