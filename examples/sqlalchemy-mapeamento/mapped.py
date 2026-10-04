"""`Mapped[T]` decide tipo e nulidade; `mapped_column` só ajusta."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.orm.exc import MappedAnnotationError
from sqlalchemy.schema import CreateTable


class Base(DeclarativeBase):
    """Base declarativa sem nada configurado."""


class ProductModel(Base):
    """Produto com um tipo Python por coluna."""

    __tablename__ = "product"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    description: Mapped[str | None]
    sku: Mapped[str | None] = mapped_column(nullable=False)
    price: Mapped[Decimal]
    created_at: Mapped[datetime]
    public_id: Mapped[UUID]
    stock: Mapped[int] = 0


print(CreateTable(ProductModel.__table__).compile(dialect=postgresql.dialect()))
print("colunas:", list(ProductModel.__table__.c.keys()))
print("ProductModel.stock:", ProductModel.stock)

assert ProductModel.__table__.c.name.nullable is False
assert ProductModel.__table__.c.description.nullable is True
assert ProductModel.__table__.c.sku.nullable is False
assert "stock" not in ProductModel.__table__.c

try:

    class SettingsModel(Base):
        """`dict` não tem tipo SQL padrão."""

        __tablename__ = "settings"

        id: Mapped[int] = mapped_column(primary_key=True)
        data: Mapped[dict]

except MappedAnnotationError:
    print("Mapped[dict]: MappedAnnotationError")
