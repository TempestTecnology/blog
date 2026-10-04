"""`Mapped[Enum]` padrão guarda o nome; o `BaseModel` do SDK guarda o valor."""

import asyncio
import enum

from sqlalchemy import text
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import CreateTable
from tempest_fastapi_sdk.db import BaseModel


class Status(enum.Enum):
    """Status de uma conta."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


class PlainBase(DeclarativeBase):
    """Base sem `type_annotation_map`."""


class PlainAccountModel(PlainBase):
    """Enum com o tipo padrão do SQLAlchemy."""

    __tablename__ = "plain_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[Status]


class AccountModel(BaseModel):
    """Enum pelo `BaseModel` do `tempest-fastapi-sdk`."""

    status: Mapped[Status]


print(CreateTable(PlainAccountModel.__table__).compile(dialect=sqlite.dialect()))
print(CreateTable(AccountModel.__table__).compile(dialect=sqlite.dialect()))
print(CreateTable(AccountModel.__table__).compile(dialect=postgresql.dialect()))


async def main() -> None:
    """Grava o mesmo membro nos dois models e lê o que foi parar no banco."""
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(PlainBase.metadata.create_all)
        await connection.run_sync(BaseModel.metadata.create_all)

    session_factory = async_sessionmaker(engine)
    async with session_factory() as session:
        session.add_all([PlainAccountModel(status=Status.ACTIVE), AccountModel(status=Status.ACTIVE)])
        await session.commit()
        plain = (await session.execute(text("SELECT status FROM plain_account"))).scalar()
        sdk = (await session.execute(text("SELECT status FROM account"))).scalar()
        print("padrão grava:", plain, "| SDK grava:", sdk)
        assert (plain, sdk) == ("ACTIVE", "active")

    await engine.dispose()


asyncio.run(main())
