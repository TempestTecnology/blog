"""Chave composta, índice parcial, `unique` + `index` e `NULLS NOT DISTINCT`."""

from sqlalchemy import ForeignKeyConstraint, Index, MetaData, PrimaryKeyConstraint, UniqueConstraint, text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import CreateIndex, CreateTable
from tempest_fastapi_sdk.db import NAMING_CONVENTION


def render(table: object, dialect: object) -> str:
    """Compila o `CREATE TABLE` e os `CREATE INDEX` para um dialeto.

    Args:
        table (object): A `Table` do model.
        dialect (object): O módulo do dialeto (`postgresql`, `sqlite`).

    Returns:
        O DDL completo.
    """
    statements = [CreateTable(table)] + [CreateIndex(index) for index in sorted(table.indexes, key=str)]
    return "\n".join(str(item.compile(dialect=dialect.dialect())).strip() for item in statements)


class Base(DeclarativeBase):
    """Base com a convenção do SDK."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class OrderLineModel(Base):
    """Linha de pedido: chave composta, SKU único entre as ativas."""

    __tablename__ = "order_line"
    __table_args__ = (
        PrimaryKeyConstraint("order_id", "position"),
        Index(
            "ix_order_line_sku_active",
            "sku",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
            sqlite_where=text("deleted_at IS NULL"),
        ),
        UniqueConstraint("coupon", postgresql_nulls_not_distinct=True),
    )

    order_id: Mapped[int]
    position: Mapped[int]
    sku: Mapped[str] = mapped_column(index=True, unique=True)
    coupon: Mapped[str | None]
    deleted_at: Mapped[str | None]


class ShipmentModel(Base):
    """Envio que aponta para uma linha pela chave composta."""

    __tablename__ = "shipment"
    __table_args__ = (
        ForeignKeyConstraint(
            ["order_id", "line_position"],
            ["order_line.order_id", "order_line.position"],
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int]
    line_position: Mapped[int]


print(render(OrderLineModel.__table__, postgresql))
print()
print(render(OrderLineModel.__table__, sqlite))
print()
print(render(ShipmentModel.__table__, postgresql))
