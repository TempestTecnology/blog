"""`model_copy`: rasa por padrão, e o `update` não valida nem entende alias."""

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    """Usuário com alias e lista."""

    id: int
    name: str = Field(alias="fullName")
    tags: list[str] = Field(default_factory=list)


ana = UserSchema(id=1, fullName="Ana", tags=["a"])

shallow = ana.model_copy()
shallow.tags.append("b")
print("cópia rasa:", ana.tags)
assert ana.tags == ["a", "b"]

deep = ana.model_copy(deep=True)
deep.tags.append("c")
assert ana.tags == ["a", "b"]

unchecked = ana.model_copy(update={"id": "não é int"})
print("update sem validação:", repr(unchecked.id))
assert unchecked.id == "não é int"

by_alias = ana.model_copy(update={"fullName": "Bia"})
print("update por alias:", by_alias.name, by_alias.model_dump())
assert by_alias.name == "Ana"
