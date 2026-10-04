"""`exclude`, `exclude_if` e `repr`: o que sai no dump, no schema e no `repr`."""

from pydantic import BaseModel, Field


class SessionSchema(BaseModel):
    """Sessão com segredo, nota opcional e token fora do `repr`."""

    password_hash: str = Field(exclude=True)
    note: str | None = Field(default=None, exclude_if=lambda value: value is None)
    token: str = Field(repr=False)


session = SessionSchema(password_hash="$2b$...", token="abc")
print(repr(session))
print(session.model_dump())

assert session.model_dump() == {"token": "abc"}
assert SessionSchema(password_hash="x", token="t", note="oi").model_dump() == {"note": "oi", "token": "t"}
assert "token" not in repr(session)
assert "password_hash" in repr(session)

validation = list(SessionSchema.model_json_schema()["properties"])
serialization = list(SessionSchema.model_json_schema(mode="serialization")["properties"])
print("schema de entrada:", validation)
print("schema de saída:", serialization)
assert "password_hash" in validation
assert "password_hash" not in serialization
