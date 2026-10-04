"""`by_alias=None` segue o `serialize_by_alias` do `model_config`."""

from pydantic import BaseModel, ConfigDict, Field


class DefaultSchema(BaseModel):
    """Sem configuração: dump usa o nome do campo."""

    user_id: int = Field(alias="userId")


class AliasByDefaultSchema(BaseModel):
    """`serialize_by_alias=True`: dump usa o alias sem precisar pedir."""

    model_config = ConfigDict(serialize_by_alias=True)

    user_id: int = Field(alias="userId")


default = DefaultSchema(userId=1)
by_config = AliasByDefaultSchema(userId=1)
print(default.model_dump(), default.model_dump(by_alias=True))
print(by_config.model_dump(), by_config.model_dump(by_alias=False))

assert default.model_dump() == {"user_id": 1}
assert default.model_dump(by_alias=True) == {"userId": 1}
assert by_config.model_dump() == {"userId": 1}
assert by_config.model_dump(by_alias=False) == {"user_id": 1}
