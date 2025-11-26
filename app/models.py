import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database import Base


class SourceOperatorConfig(Base):  # Промежуточная таблица для связи Оператор <-> Источник с весом
    __tablename__ = "source_operator_configs"

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), primary_key=True)
    operator_id: Mapped[int] = mapped_column(ForeignKey("operators.id"), primary_key=True)
    weight: Mapped[int] = mapped_column(Integer, default=1)  # Вес (компетенция) оператора на этом источнике.

    # Связи
    operator: Mapped["Operator"] = relationship(back_populates="source_configs")
    source: Mapped["Source"] = relationship(back_populates="operator_configs")


class Operator(Base):  # Основные сущности
    __tablename__ = "operators"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    max_load: Mapped[int] = mapped_column(Integer, default=5)  # Лимит активных обращений

    # Связи
    source_configs: Mapped[List["SourceOperatorConfig"]] = relationship(
        back_populates="operator")  # Связь с конфигами источников
    inquiries: Mapped[List["Inquiry"]] = relationship(back_populates="operator")  # Связь с обращениями


class Source(Base):  # Источник трафика
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True)

    operator_configs: Mapped[List["SourceOperatorConfig"]] = relationship(back_populates="source")  # Связь с конфигами


class Lead(Base):
    """Конечный клиент"""
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    client_id: Mapped[str] = mapped_column(String, unique=True, index=True)  # Уникальный идентификатор клиента

    # Связь
    inquiries: Mapped[List["Inquiry"]] = relationship(back_populates="lead")  # Связь с историей обращений


class Inquiry(Base):
    """Конкретное обращение (заявка)"""
    __tablename__ = "inquiries"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(Boolean,
                                            default=True)  # Статус активности. True = в работе (занимает слот нагрузки), False = закрыто.

    # Внешние ключи
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id"))
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"))
    operator_id: Mapped[Optional[int]] = mapped_column(ForeignKey("operators.id"),
                                                       nullable=True)  # Оператор может быть NULL, если подходящего не нашлось

    # ORM связи
    lead: Mapped["Lead"] = relationship(back_populates="inquiries")
    operator: Mapped["Operator"] = relationship(back_populates="inquiries")
    source: Mapped["Source"] = relationship()
