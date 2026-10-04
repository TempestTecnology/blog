"""`default` mora no Python; `server_default` mora no banco."""

import asyncio
from datetime import datetime

from sqlalchemy import func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import ArgumentError, IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import CreateTable


class Base(DeclarativeBase):
    """Base declarativa."""


class TaskModel(Base):
    """Tarefa com cada tipo de default."""

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    priority: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(server_default="open")
    attempts: Mapped[int] = mapped_column(server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


print(CreateTable(TaskModel.__table__).compile(dialect=postgresql.dialect()))

try:

    class BrokenModel(Base):
        """`server_default` com `int` cru."""

        __tablename__ = "broken"

        id: Mapped[int] = mapped_column(primary_key=True)
        attempts: Mapped[int] = mapped_column(server_default=0)

except ArgumentError:
    print("server_default=0: ArgumentError — use \"0\" ou text(\"0\")")


async def main() -> None:
    """Insere pelo ORM e por SQL cru, e compara."""
    engine = create_async_engine("sqlite+aiosqlite://")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        task = TaskModel()
        session.add(task)
        await session.flush()
        print("pelo ORM:", task.priority, task.status, task.attempts)
        assert (task.priority, task.status, task.attempts) == (1, "open", 0)

        try:
            await session.execute(text("INSERT INTO task (status) VALUES ('open')"))
        except IntegrityError as error:
            print("SQL cru:", error.orig)

    await engine.dispose()


asyncio.run(main())
