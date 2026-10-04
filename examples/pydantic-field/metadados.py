"""Parâmetros que só mudam o JSON Schema (e o Swagger do FastAPI)."""

import json
import warnings

from pydantic import BaseModel, Field


class ProductSchema(BaseModel):
    """Produto documentado campo a campo."""

    name: str = Field(title="Nome", description="Nome exibido na vitrine.", examples=["Café"])
    unit_price: int = Field(
        field_title_generator=lambda field_name, info: field_name.replace("_", " ").title(),
        json_schema_extra={"x-unit": "centavos"},
    )
    stock: int = Field(default=0, json_schema_extra=lambda schema: schema.update({"minimum": 0}))
    old_price: int | None = Field(default=None, deprecated="Use unit_price.")


properties = ProductSchema.model_json_schema()["properties"]
print(json.dumps(properties, indent=2, ensure_ascii=False))

assert properties["name"]["title"] == "Nome"
assert properties["unit_price"]["title"] == "Unit Price"
assert properties["unit_price"]["x-unit"] == "centavos"
assert properties["stock"]["minimum"] == 0
assert properties["old_price"]["deprecated"] is True

product = ProductSchema(name="Café", unit_price=990, old_price=1200)
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    assert product.old_price == 1200
    print("ao ler old_price:", caught[0].message)
