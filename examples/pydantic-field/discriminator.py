"""`discriminator`: a união olha uma chave e vai direto ao tipo certo."""

from typing import Literal

from pydantic import BaseModel, Field, ValidationError


class PixSchema(BaseModel):
    """Pagamento por Pix."""

    method: Literal["pix"]
    key: str


class CardSchema(BaseModel):
    """Pagamento por cartão."""

    method: Literal["card"]
    last4: str


class TaggedSchema(BaseModel):
    """União discriminada por `method`."""

    payment: PixSchema | CardSchema = Field(discriminator="method")


class PlainSchema(BaseModel):
    """A mesma união, sem discriminador."""

    payment: PixSchema | CardSchema


payload = {"payment": {"method": "card"}}

for schema in (TaggedSchema, PlainSchema):
    try:
        schema.model_validate(payload)
    except ValidationError as error:
        print(schema.__name__, [(item["type"], item["loc"]) for item in error.errors()])

print(TaggedSchema.model_validate({"payment": {"method": "pix", "key": "a@b.com"}}))
