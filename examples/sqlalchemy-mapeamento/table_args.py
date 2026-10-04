"""As formas válidas de `__table_args__` — e as três que quebram."""

from sqlalchemy import UniqueConstraint
from sqlalchemy.exc import ArgumentError, ConstraintColumnNotFoundError
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa."""


class InvoiceModel(Base):
    """Tupla de constraints, com o `dict` de opções no fim."""

    __tablename__ = "invoice"
    __table_args__ = (
        UniqueConstraint("number", "series"),
        {"schema": "billing", "comment": "Notas fiscais emitidas"},
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int]
    series: Mapped[str]
    email: Mapped[str] = mapped_column("email_address")


print(InvoiceModel.__table__.fullname, "|", InvoiceModel.__table__.comment)
assert InvoiceModel.__table__.fullname == "billing.invoice"


def no_trailing_comma() -> None:
    """Parênteses sem vírgula não fazem tupla."""

    class AModel(Base):
        """Constraint solta."""

        __tablename__ = "a"
        __table_args__ = (UniqueConstraint("code"))

        id: Mapped[int] = mapped_column(primary_key=True)
        code: Mapped[str]


def dict_first() -> None:
    """O `dict` precisa ser o último item."""

    class BModel(Base):
        """`dict` antes da constraint."""

        __tablename__ = "b"
        __table_args__ = ({"comment": "x"}, UniqueConstraint("code"))

        id: Mapped[int] = mapped_column(primary_key=True)
        code: Mapped[str]


def attribute_name() -> None:
    """Constraint cita a coluna do banco, não o atributo Python."""

    class CModel(Base):
        """Atributo `email`, coluna `email_address`."""

        __tablename__ = "c"
        __table_args__ = (UniqueConstraint("email"),)

        id: Mapped[int] = mapped_column(primary_key=True)
        email: Mapped[str] = mapped_column("email_address")


for attempt in (no_trailing_comma, dict_first, attribute_name):
    try:
        attempt()
    except (ArgumentError, ConstraintColumnNotFoundError) as error:
        print(f"{attempt.__name__:18}", type(error).__name__)
