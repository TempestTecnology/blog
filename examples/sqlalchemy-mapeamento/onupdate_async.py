"""`onupdate` com expressão SQL expira o atributo — e em async isso é `MissingGreenlet`."""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.exc import StatementError
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    """Agora, em UTC.

    Returns:
        O instante atual com fuso UTC.
    """
    return datetime.now(UTC)


class Base(AsyncAttrs, DeclarativeBase):
    """Base com `AsyncAttrs`, que dá o `awaitable_attrs`."""


class OrderModel(Base):
    """Pedido com dois `onupdate`: um no banco, outro no Python."""

    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="open")
    sql_updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())
    py_updated_at: Mapped[datetime | None] = mapped_column(onupdate=utcnow)


class EagerOrderModel(Base):
    """O mesmo `onupdate` SQL, com `eager_defaults=True`."""

    __tablename__ = "eager_orders"
    __mapper_args__ = {"eager_defaults": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(default="open")
    sql_updated_at: Mapped[datetime | None] = mapped_column(onupdate=func.now())


async def main() -> None:
    """Atualiza e tenta ler cada timestamp."""
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        order = OrderModel()
        session.add(order)
        await session.flush()
        order.status = "paid"
        await session.flush()

        print("py_updated_at:", order.py_updated_at is not None)
        try:
            order.sql_updated_at
        except StatementError as error:
            print("sql_updated_at:", type(error.orig).__name__)

        print("awaitable_attrs:", await order.awaitable_attrs.sql_updated_at is not None)

        eager = EagerOrderModel()
        session.add(eager)
        await session.flush()
        eager.status = "paid"
        await session.flush()
        print("eager_defaults=True:", eager.sql_updated_at is not None)

    await engine.dispose()


asyncio.run(main())
