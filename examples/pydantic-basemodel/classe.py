"""Metadados da classe: o que o Pydantic guarda ao criar o model."""

import warnings
from typing import Any, ClassVar

from pydantic import BaseModel, Field, PrivateAttr, RootModel, computed_field, field_validator


class ProductSchema(BaseModel):
    """Produto com um pouco de tudo."""

    currency: ClassVar[str] = "BRL"

    sku: str
    name: str = Field(alias="displayName")
    cents: int = 0
    _views: int = PrivateAttr(default=0)

    @field_validator("sku")
    @classmethod
    def upper_sku(cls, value: str) -> str:
        """Normaliza o SKU.

        Args:
            value (str): SKU recebido.

        Returns:
            O SKU em maiúsculas.
        """
        return value.upper()

    @computed_field
    @property
    def price(self) -> str:
        """Preço formatado.

        Returns:
            O preço em reais.
        """
        return f"{self.cents / 100:.2f}"

    def model_post_init(self, context: Any, /) -> None:
        """Gancho pós-validação, vazio de propósito.

        Args:
            context (Any): Contexto da validação.
        """


print("model_fields:", list(ProductSchema.model_fields))
print("model_computed_fields:", list(ProductSchema.model_computed_fields))
print("__class_vars__:", ProductSchema.__class_vars__)
print("__private_attributes__:", list(ProductSchema.__private_attributes__))
print("__signature__:", ProductSchema.__signature__)
print("field_validators:", list(ProductSchema.__pydantic_decorators__.field_validators))
print("__pydantic_post_init__:", ProductSchema.__pydantic_post_init__)
print("__pydantic_custom_init__:", ProductSchema.__pydantic_custom_init__)
print("__pydantic_root_model__:", ProductSchema.__pydantic_root_model__, RootModel[list[int]].__pydantic_root_model__)

assert ProductSchema.__pydantic_fields__ is ProductSchema.model_fields
assert "displayName" in str(ProductSchema.__signature__)

product = ProductSchema(sku="abc", displayName="Café")
with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    list(product.model_fields)
    print("model_fields na instância:", type(caught[0].message).__name__)
