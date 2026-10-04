"""`serialize_as_any` é duck typing; `polymorphic_serialization` só segue subclasse."""

from pydantic import BaseModel


class UserSchema(BaseModel):
    """Usuário público."""

    name: str


class AdminSchema(UserSchema):
    """Subclasse com um campo a mais."""

    level: int


class LeakySchema(BaseModel):
    """Model sem relação com `UserSchema`, com um segredo."""

    name: str
    password_hash: str


class TeamSchema(BaseModel):
    """Time cujo líder é declarado como `UserSchema`."""

    lead: UserSchema


team = TeamSchema(lead=AdminSchema(name="Ana", level=9))
print(team.model_dump())
print(team.model_dump(polymorphic_serialization=True))
print(team.model_dump(serialize_as_any=True))

assert team.model_dump() == {"lead": {"name": "Ana"}}
assert team.model_dump(polymorphic_serialization=True) == {"lead": {"name": "Ana", "level": 9}}
assert team.model_dump(serialize_as_any=True) == {"lead": {"name": "Ana", "level": 9}}

leaky = TeamSchema.model_construct(lead=LeakySchema(name="Bia", password_hash="$2b$..."))
print(leaky.model_dump(polymorphic_serialization=True))
print(leaky.model_dump(serialize_as_any=True))

assert leaky.model_dump(polymorphic_serialization=True) == {"lead": {"name": "Bia"}}
assert leaky.model_dump(serialize_as_any=True) == {"lead": {"name": "Bia", "password_hash": "$2b$..."}}
