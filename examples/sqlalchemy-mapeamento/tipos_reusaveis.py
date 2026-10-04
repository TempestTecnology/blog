"""`type_annotation_map` e `Annotated`: declarar o tipo uma vez só."""

from typing import Annotated

from sqlalchemy import String
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import CreateTable

IntPk = Annotated[int, mapped_column(primary_key=True)]
Str50 = Annotated[str, mapped_column(String(50))]


class Base(DeclarativeBase):
    """Todo `Mapped[str]` vira `VARCHAR(255)`."""

    type_annotation_map = {str: String(255)}


class CustomerModel(Base):
    """Cliente usando os tipos reaproveitáveis."""

    __tablename__ = "customer"

    id: Mapped[IntPk]
    name: Mapped[str]
    document: Mapped[Str50]
    nickname: Mapped[Str50 | None]
    uf: Mapped[str] = mapped_column(String(2))


print(CreateTable(CustomerModel.__table__).compile(dialect=postgresql.dialect()))

columns = CustomerModel.__table__.c
assert columns.name.type.length == 255
assert columns.document.type.length == 50
assert columns.nickname.nullable is True
assert columns.uf.type.length == 2
