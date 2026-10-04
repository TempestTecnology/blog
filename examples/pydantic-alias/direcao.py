"""Os três parâmetros de alias e a direção em que cada um age."""

from pydantic import BaseModel, Field, ValidationError


class AliasSchema(BaseModel):
    """`alias` vale na entrada e na saída."""

    user_id: int = Field(alias="userId")


class ValidationAliasSchema(BaseModel):
    """`validation_alias` vale só na entrada."""

    user_id: int = Field(validation_alias="userId")


class SerializationAliasSchema(BaseModel):
    """`serialization_alias` vale só na saída."""

    user_id: int = Field(serialization_alias="userId")


assert AliasSchema.model_validate({"userId": 1}).model_dump(by_alias=True) == {"userId": 1}
assert ValidationAliasSchema.model_validate({"userId": 1}).model_dump(by_alias=True) == {"user_id": 1}
assert SerializationAliasSchema.model_validate({"user_id": 1}).model_dump(by_alias=True) == {"userId": 1}

for schema in (AliasSchema, ValidationAliasSchema):
    try:
        schema.model_validate({"user_id": 1})
    except ValidationError as error:
        print(schema.__name__, "recusou user_id:", error.errors()[0]["type"])

print(AliasSchema.model_validate({"userId": 1}).model_dump())
