from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):  # Базовый класс настройки pydantic
    model_config = ConfigDict(from_attributes=True)


# Операторы
class OperatorCreate(BaseSchema):
    name: str = Field(..., min_length=1, description="Имя оператора")
    max_load: int = Field(5, ge=0, description="Максимальное кол-во активных диалогов")
    is_active: bool = Field(True, description="Может ли принимать заявки")


class OperatorUpdate(BaseSchema):
    # Поля опциональны, чтобы можно было обновить только одно из них
    max_load: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class OperatorRead(OperatorCreate):
    id: int


# Источники
class SourceCreate(BaseSchema):
    name: str = Field(..., min_length=1, description="Название источника/бота")


class SourceRead(SourceCreate):
    id: int


# Настройка весов
class OperatorWeight(BaseSchema):
    operator_id: int
    weight: int = Field(..., ge=1, description="Вес компетенции (доля трафика)")


class SourceConfigUpdate(BaseSchema):
    configs: List[OperatorWeight]


# Лиды
class LeadRead(BaseSchema):
    id: int
    client_id: str


# Обращения

class InquiryCreate(BaseSchema):
    client_id: str = Field(..., description="Уникальный ID клиента (телефон/email)")
    source_id: int = Field(..., description="ID источника, откуда пришло сообщение")


class InquiryRead(BaseSchema):
    id: int
    created_at: datetime
    is_active: bool

    lead_id: int
    source_id: int
    operator_id: Optional[int] = None  # Может быть None, если оператор не найден
