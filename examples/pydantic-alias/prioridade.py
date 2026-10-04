"""`alias_priority` decide se o `alias_generator` pode sobrescrever o `Field`."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ProductSchema(BaseModel):
    """Gerador `to_camel` ativo, com três formas de declarar o campo."""

    model_config = ConfigDict(alias_generator=to_camel)

    unit_price: int = Field(alias="PRICE")
    stock_count: int = Field(alias="STOCK", alias_priority=1)
    created_by: int


for name, field in ProductSchema.model_fields.items():
    print(f"{name:12} alias={field.alias!r:14} alias_priority={field.alias_priority}")

assert ProductSchema.model_fields["unit_price"].alias == "PRICE"
assert ProductSchema.model_fields["stock_count"].alias == "stockCount"
assert ProductSchema.model_fields["created_by"].alias == "createdBy"
