"""As três portas de entrada: `model_validate`, `model_validate_json`, `model_validate_strings`."""

from datetime import date

from pydantic import BaseModel, Field, ValidationError


class UserSchema(BaseModel):
    """Usuário com alias e data."""

    id: int
    name: str = Field(alias="fullName")
    born: date | None = None


class UserRow:
    """Objeto com atributos, como uma linha do ORM."""

    id: int = 1
    fullName: str = "Ana"


print(UserSchema.model_validate({"id": "1", "fullName": "Ana"}))
print(UserSchema.model_validate({"id": 1, "name": "Ana"}, by_name=True))
print(UserSchema.model_validate(UserRow(), from_attributes=True))
print(UserSchema.model_validate_json('{"id": 1, "fullName": "Ana", "born": "2000-01-31"}'))
print(UserSchema.model_validate_strings({"id": "1", "fullName": "Ana", "born": "2000-01-31"}, strict=True))

attempts = {
    "strict=True, id='1'": lambda: UserSchema.model_validate({"id": "1", "fullName": "Ana"}, strict=True),
    "extra='forbid' na chamada": lambda: UserSchema.model_validate({"id": 1, "fullName": "Ana", "x": 1}, extra="forbid"),
    "objeto sem from_attributes": lambda: UserSchema.model_validate(UserRow()),
    "strict, data como str": lambda: UserSchema.model_validate({"id": 1, "fullName": "Ana", "born": "2000-01-31"}, strict=True),
    "validate_strings com int": lambda: UserSchema.model_validate_strings({"id": 1, "fullName": "Ana"}),
}
for label, attempt in attempts.items():
    try:
        attempt()
    except ValidationError as error:
        print(f"{label:28}", error.errors()[0]["type"])
