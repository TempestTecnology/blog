"""`exclude_defaults` compara com o default; `exclude_none` só olha campos."""

from typing import Any

from pydantic import BaseModel, Field


class ProfileSchema(BaseModel):
    """Perfil com defaults e valores opcionais."""

    name: str
    bio: str | None = None
    tags: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


explicit = ProfileSchema(name="Ana", bio=None, tags=[])
print(explicit.model_dump(exclude_unset=True), explicit.model_dump(exclude_defaults=True))
assert explicit.model_dump(exclude_unset=True) == {"name": "Ana", "bio": None, "tags": []}
assert explicit.model_dump(exclude_defaults=True) == {"name": "Ana"}

nested_none = ProfileSchema(name="Ana", meta={"avatar": None})
print(nested_none.model_dump(exclude_none=True))
assert nested_none.model_dump(exclude_none=True) == {"name": "Ana", "tags": [], "meta": {"avatar": None}}
