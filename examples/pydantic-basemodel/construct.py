"""`model_construct` pula a validação — e o `__init__` customizado."""

from typing import Any

from pydantic import BaseModel, Field, field_validator


class UserSchema(BaseModel):
    """Usuário com validator e `__init__` próprio."""

    id: int
    name: str = Field(alias="fullName")
    tags: list[str] = Field(default_factory=list)

    def __init__(self, **data: Any) -> None:
        """Registra cada chamada antes de delegar ao Pydantic.

        Args:
            **data (Any): Campos do usuário.
        """
        CALLS.append("__init__")
        super().__init__(**data)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        """Tira espaço das pontas.

        Args:
            value (str): Nome recebido.

        Returns:
            O nome sem espaço nas pontas.
        """
        return value.strip()


CALLS: list[str] = []

built = UserSchema.model_construct(id="não é int", fullName="  Ana  ")
print(built, built.model_fields_set, CALLS)

assert built.id == "não é int"
assert built.name == "  Ana  "
assert built.tags == []
assert built.model_fields_set == {"id", "name"}
assert CALLS == []

UserSchema.model_validate({"id": 1, "fullName": "Ana"})
UserSchema.model_validate_json('{"id": 1, "fullName": "Ana"}')
assert CALLS == ["__init__", "__init__"]

partial = UserSchema.model_construct(_fields_set={"id"}, id=1, fullName="Ana")
assert partial.model_dump(exclude_unset=True) == {"id": 1}
