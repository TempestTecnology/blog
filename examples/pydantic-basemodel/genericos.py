"""Model genérico: `__pydantic_generic_metadata__` e `model_parametrized_name`."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PageSchema(BaseModel, Generic[T]):
    """Página genérica, com o nome padrão."""

    items: list[T]


class NamedPageSchema(BaseModel, Generic[T]):
    """Página genérica com nome customizado no schema."""

    items: list[T]

    @classmethod
    def model_parametrized_name(cls, params: tuple[type[Any], ...]) -> str:
        """Gera `IntPage` em vez de `NamedPageSchema[int]`.

        Args:
            params (tuple[type[Any], ...]): Os tipos usados na parametrização.

        Returns:
            O nome da classe parametrizada.
        """
        return f"{params[0].__name__.title()}Page"


print(PageSchema[int].__name__, NamedPageSchema[int].__name__)
print(PageSchema.__pydantic_generic_metadata__)
print(PageSchema[int].__pydantic_generic_metadata__)
print(NamedPageSchema[int].model_json_schema()["title"])
print(PageSchema[int](items=["1", 2]))

assert NamedPageSchema[int].__name__ == "IntPage"
