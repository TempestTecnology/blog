"""`__pydantic_init_subclass__` x `__pydantic_on_complete__`."""

from typing import Any

from pydantic import BaseModel

EVENTS: list[str] = []


class RegisteredSchema(BaseModel):
    """Base que registra cada subclasse nos dois ganchos."""

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Any) -> None:
        """Roda ao criar a subclasse, completa ou não.

        Args:
            **kwargs (Any): Argumentos de classe repassados pelo Python.
        """
        EVENTS.append(f"init_subclass:{cls.__name__}")

    @classmethod
    def __pydantic_on_complete__(cls) -> None:
        """Roda quando a classe está pronta para validar."""
        EVENTS.append(f"on_complete:{cls.__name__}")


class OrderSchema(RegisteredSchema):
    """Completa na hora."""

    id: int


class ShipmentSchema(RegisteredSchema):
    """Depende de um tipo ainda não definido."""

    address: "AddressSchema"


print(EVENTS)
assert "init_subclass:ShipmentSchema" in EVENTS
assert "on_complete:ShipmentSchema" not in EVENTS


class AddressSchema(BaseModel):
    """O tipo que faltava."""

    city: str


ShipmentSchema.model_rebuild()
print(EVENTS)
assert EVENTS[-1] == "on_complete:ShipmentSchema"
