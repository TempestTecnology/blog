"""Constraints com e sem `naming_convention` — e o que exige nome."""

from sqlalchemy import CheckConstraint, ForeignKey, Index, MetaData, String, UniqueConstraint, func, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import InvalidRequestError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import CreateIndex, CreateTable
from tempest_fastapi_sdk.db import NAMING_CONVENTION


def render(table: object) -> str:
    """Compila o `CREATE TABLE` e os `CREATE INDEX` para PostgreSQL.

    Args:
        table (object): A `Table` do model.

    Returns:
        O DDL completo.
    """
    statements = [CreateTable(table)] + [CreateIndex(index) for index in sorted(table.indexes, key=str)]
    return "\n".join(str(item.compile(dialect=postgresql.dialect())).strip() for item in statements)


class PlainBase(DeclarativeBase):
    """Sem convenção: o banco escolhe os nomes."""


class ConventionBase(DeclarativeBase):
    """Com a convenção do `tempest-fastapi-sdk`."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def build(base: type[DeclarativeBase], prefix: str) -> type:
    """Declara o mesmo par de tabelas sobre uma base.

    Args:
        base (type[DeclarativeBase]): A base declarativa.
        prefix (str): Prefixo dos nomes de tabela, para as duas bases não colidirem.

    Returns:
        O model de usuário.
    """

    class OrgModel(base):
        """Organização."""

        __tablename__ = f"{prefix}org"

        id: Mapped[int] = mapped_column(primary_key=True)

    class UserModel(base):
        """Usuário, único por e-mail dentro da organização."""

        __tablename__ = f"{prefix}users"
        __table_args__ = (
            UniqueConstraint("org_id", "email"),
            CheckConstraint("age >= 0", name="age_non_negative"),
            Index(f"ix_{prefix}users_email_lower", func.lower(text("email"))),
        )

        id: Mapped[int] = mapped_column(primary_key=True)
        org_id: Mapped[int] = mapped_column(ForeignKey(f"{prefix}org.id", ondelete="CASCADE"), index=True)
        email: Mapped[str] = mapped_column(String(255))
        document: Mapped[str] = mapped_column(String(14), unique=True)
        age: Mapped[int]

    return UserModel


print(render(build(PlainBase, "").__table__))
print()
print(render(build(ConventionBase, "c_").__table__))

try:

    class ScoreModel(ConventionBase):
        """`CheckConstraint` sem nome, sob a convenção."""

        __tablename__ = "score"
        __table_args__ = (CheckConstraint("value > 0"),)

        id: Mapped[int] = mapped_column(primary_key=True)
        value: Mapped[int]

except InvalidRequestError as error:
    print("\nCheckConstraint sem nome:", error)


class TagModel(ConventionBase):
    """Índice funcional sem nome, e `func.lower` com string crua."""

    __tablename__ = "tag"
    __table_args__ = (
        Index(None, func.lower(text("slug"))),
        Index("ix_tag_title_lower", func.lower("title")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str]
    title: Mapped[str]


print("\níndices da tag:", sorted(index.name for index in TagModel.__table__.indexes))
print(render(TagModel.__table__).split("\n")[-1])
