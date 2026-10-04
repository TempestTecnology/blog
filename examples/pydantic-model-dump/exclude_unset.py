"""`exclude_unset` e as duas pegadinhas de um PATCH com o `BaseSchema`."""

from pydantic import Field
from tempest_fastapi_sdk import BaseSchema


class UserUpdateSchema(BaseSchema):
    """Payload de PATCH: tudo opcional."""

    name: str | None = None
    bio: str | None = None
    tags: list[str] = Field(default_factory=list)


clear_bio = UserUpdateSchema.model_validate({"bio": None})
print(clear_bio.model_fields_set)
print(clear_bio.model_dump(exclude_unset=True), clear_bio.to_dict())

assert clear_bio.model_fields_set == {"bio"}
assert clear_bio.model_dump(exclude_unset=True) == {"bio": None}
assert clear_bio.to_dict() == {}

mutated = UserUpdateSchema.model_validate({"name": "Ana"})
mutated.tags.append("admin")
print(mutated.model_dump(exclude_unset=True))
assert mutated.model_dump(exclude_unset=True) == {"name": "Ana"}

mutated.tags = [*mutated.tags, "staff"]
print(mutated.model_dump(exclude_unset=True))
assert mutated.model_dump(exclude_unset=True) == {"name": "Ana", "tags": ["admin", "staff"]}
