"""No SQLite, `FOREIGN KEY` e `ON DELETE CASCADE` vêm desligados."""

import asyncio

from sqlalchemy import CheckConstraint, ForeignKey, event, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa."""


class OrgModel(Base):
    """Organização."""

    __tablename__ = "org"

    id: Mapped[int] = mapped_column(primary_key=True)


class MemberModel(Base):
    """Membro, apagado junto com a organização."""

    __tablename__ = "member"
    __table_args__ = (CheckConstraint("age >= 0", name="age_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("org.id", ondelete="CASCADE"))
    email: Mapped[str | None] = mapped_column(unique=True)
    age: Mapped[int] = mapped_column(default=0)


def enable_foreign_keys(engine: AsyncEngine) -> None:
    """Liga `PRAGMA foreign_keys` em toda conexão nova do engine.

    Args:
        engine (AsyncEngine): O engine SQLite.
    """

    @event.listens_for(engine.sync_engine, "connect")
    def _on_connect(dbapi_connection: object, _: object) -> None:
        """Executa o pragma na conexão crua do driver.

        Args:
            dbapi_connection (object): A conexão DBAPI recém-aberta.
            _ (object): O registro do pool, não usado.
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


async def run(foreign_keys: bool) -> None:
    """Testa FK, CHECK, UNIQUE com NULL e CASCADE.

    Args:
        foreign_keys (bool): Se liga o pragma.
    """
    engine = create_async_engine("sqlite+aiosqlite://")
    if foreign_keys:
        enable_foreign_keys(engine)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    label = "pragma ligado " if foreign_keys else "pragma padrão "
    session_factory = async_sessionmaker(engine)
    async with session_factory() as session:
        session.add(MemberModel(org_id=999, email="orfao@x.com"))
        try:
            await session.commit()
            print(label, "FK para org inexistente: aceito")
        except IntegrityError as error:
            print(label, "FK:", error.orig)
            await session.rollback()

        session.add_all([OrgModel(id=1), MemberModel(org_id=1)])
        try:
            await session.commit()
            print(label, "org e membro no mesmo flush, sem relationship(): aceito")
        except IntegrityError as error:
            print(label, "org e membro no mesmo flush, sem relationship():", error.orig)
            await session.rollback()

        session.add(OrgModel(id=2))
        await session.flush()
        session.add(MemberModel(org_id=2, age=-1))
        try:
            await session.commit()
        except IntegrityError as error:
            print(label, "CHECK:", error.orig)
            await session.rollback()

        session.add(OrgModel(id=3))
        await session.flush()
        session.add_all([MemberModel(org_id=3), MemberModel(org_id=3)])
        await session.commit()
        print(label, "dois NULL em coluna unique: aceito")

        await session.execute(text("DELETE FROM org WHERE id = 3"))
        await session.commit()
        remaining = (await session.execute(text("SELECT count(*) FROM member WHERE org_id = 3"))).scalar()
        print(label, "membros da org apagada:", remaining)

    await engine.dispose()


asyncio.run(run(foreign_keys=False))
asyncio.run(run(foreign_keys=True))
