import random
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from fastapi import HTTPException
from app import models, schemas


# Вспомогательные функции
async def get_or_create_lead(db: AsyncSession, client_id: str) -> models.Lead:
    stmt = select(models.Lead).where(models.Lead.client_id == client_id)
    result = await db.execute(stmt)
    lead = result.scalar_one_or_none()

    if not lead:
        lead = models.Lead(client_id=client_id)
        db.add(lead)
        await db.flush() # Делаем flush, чтобы получить ID, коммит будет в основной транзакции

    return lead


async def get_operators_load(db: AsyncSession, operator_ids: List[int]) -> Dict[int, int]:
    """
    Возвращает текущую нагрузку (кол-во активных обращений)
    для списка операторов в формате {operator_id: count}.
    """
    if not operator_ids:
        return {}

    stmt = (
        select(models.Inquiry.operator_id, func.count(models.Inquiry.id))
        .where(
            models.Inquiry.is_active == True,
            models.Inquiry.operator_id.in_(operator_ids)
        )
        .group_by(models.Inquiry.operator_id)
    )  # Группируем активные обращения по операторам
    result = await db.execute(stmt)

    loads = {op_id: 0 for op_id in operator_ids} # Преобразуем в словарь, по умолчанию нагрузка 0
    for op_id, count in result.all():
        loads[op_id] = count

    return loads


# Основная бизнес-логика

async def create_inquiry_logic(db: AsyncSession, data: schemas.InquiryCreate) -> models.Inquiry:
    """
    Главная функция распределения:
    1. Найти/создать лида.
    2. Найти активных операторов для источника.
    3. Отфильтровать по лимиту нагрузки.
    4. Выбрать по весу.
    5. Создать обращение.
    """

    # Проверяем источник
    stmt_source = select(models.Source).where(models.Source.id == data.source_id)
    source = (await db.execute(stmt_source)).scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Получаем или создаем лида
    lead = await get_or_create_lead(db, data.client_id)

    # Ищем кандидатов (Операторы, привязанные к источнику + Активные)
    stmt_candidates = (
        select(models.Operator, models.SourceOperatorConfig.weight)
        .join(models.SourceOperatorConfig, models.Operator.id == models.SourceOperatorConfig.operator_id)
        .where(
            models.SourceOperatorConfig.source_id == data.source_id,
            models.Operator.is_active == True
        )
    )
    candidates_result = await db.execute(stmt_candidates)
    candidates = candidates_result.all()  # Список кортежей (Operator, weight)

    selected_operator_id = None

    if candidates:
        candidate_ids = [op.id for op, _ in candidates]  # Список ID кандидатов для запроса нагрузки

        # Получаем текущую нагрузку
        current_loads = await get_operators_load(db, candidate_ids)

        # Фильтрация: оставляем только тех, у кого есть место
        valid_candidates = []
        valid_weights = []

        for op, weight in candidates:
            load = current_loads.get(op.id, 0)
            if load < op.max_load:
                valid_candidates.append(op)
                valid_weights.append(weight)

        # Выбор оператора (Weighted Random)
        if valid_candidates:
            chosen_operator = random.choices(valid_candidates, weights=valid_weights, k=1)[0]
            selected_operator_id = chosen_operator.id

    # Создаем обращение
    inquiry = models.Inquiry(
        lead_id=lead.id,
        source_id=data.source_id,
        operator_id=selected_operator_id,
        is_active=True  # Считаем обращение сразу активным
    )
    db.add(inquiry)
    await db.commit()
    await db.refresh(inquiry)

    return inquiry


# Управление конфигурацией

async def update_source_config_logic(
        db: AsyncSession,
        source_id: int,
        config_data: schemas.SourceConfigUpdate
):
    """
    Полная замена конфигурации для источника.
    Удаляет старые связи и создает новые с указанными весами.
    """
    # Проверяем источник
    source_check = await db.execute(select(models.Source).where(models.Source.id == source_id))
    if not source_check.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Source not found")

    await db.execute(
        delete(models.SourceOperatorConfig).where(models.SourceOperatorConfig.source_id == source_id)
    )  # Удаляем старые конфиги для этого источника

    # Добавляем новые
    for item in config_data.configs:
        new_config = models.SourceOperatorConfig(
            source_id=source_id,
            operator_id=item.operator_id,
            weight=item.weight
        )
        db.add(new_config)

    await db.commit()
    return {"status": "updated", "count": len(config_data.configs)}