"""`init`, `init_var` e `kw_only` só valem em dataclass Pydantic."""

from dataclasses import InitVar

from pydantic import BaseModel, Field, ValidationError
from pydantic.dataclasses import dataclass


@dataclass
class UserRecord:
    """Campo keyword-only, campo só de construtor e campo fora do `__init__`."""

    raw_password: InitVar[str]
    email: str = Field(kw_only=True)
    password_hash: str = Field(default="", init=False)

    def __post_init__(self, raw_password: str) -> None:
        """Deriva o hash a partir da senha recebida só no construtor.

        Args:
            raw_password (str): Senha em texto, nunca guardada.
        """
        self.password_hash = f"hash({raw_password})"


user = UserRecord("s3cret", email="ana@x.com")
print(user)
assert user.password_hash == "hash(s3cret)"
assert not hasattr(user, "raw_password")
assert UserRecord.__pydantic_fields__["raw_password"].init_var is True

try:
    UserRecord("s3cret", "ana@x.com")
except ValidationError as error:
    print("email posicional:", [item["type"] for item in error.errors()])


@dataclass
class HandWrittenRecord:
    """`Field(init_var=True)` escrito à mão: o campo some do construtor."""

    email: str
    raw_password: str = Field(init_var=True)


try:
    HandWrittenRecord("ana@x.com", "s3cret")
except ValidationError as error:
    print("Field(init_var=True):", [item["type"] for item in error.errors()])


class IgnoredSchema(BaseModel):
    """Em `BaseModel`, `init=False` é ignorado sem aviso."""

    counter: int = Field(default=0, init=False)


print(IgnoredSchema(counter=5))
assert IgnoredSchema(counter=5).counter == 5
