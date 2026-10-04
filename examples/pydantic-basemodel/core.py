"""Por baixo: core schema, validator, serializer e o JSON Schema."""

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    """Usuário com alias."""

    user_id: int = Field(alias="userId")


print(UserSchema.__pydantic_core_schema__["type"])
print(type(UserSchema.__pydantic_validator__).__name__, type(UserSchema.__pydantic_serializer__).__name__)

user = UserSchema.__pydantic_validator__.validate_python({"userId": 1})
print(user, UserSchema.__pydantic_serializer__.to_python(user))
assert user == UserSchema.model_validate({"userId": 1})

print("model_dump():", user.model_dump())
print("model_json_schema():", list(UserSchema.model_json_schema()["properties"]))
assert list(user.model_dump()) == ["user_id"]
assert list(UserSchema.model_json_schema()["properties"]) == ["userId"]
