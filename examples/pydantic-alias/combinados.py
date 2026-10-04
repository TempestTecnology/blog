"""`alias` junto de `validation_alias`, mais `AliasChoices` e `AliasPath`."""

from pydantic import AliasChoices, AliasPath, BaseModel, Field


class OrderSchema(BaseModel):
    """`alias` preenche os dois lados; `validation_alias` toma a entrada."""

    order_id: int = Field(alias="orderId", validation_alias="ORDER_ID")


class CustomerSchema(BaseModel):
    """Vários nomes aceitos na entrada, e um caminho aninhado."""

    customer_id: int = Field(validation_alias=AliasChoices("customer_id", "ID"))
    city: str = Field(validation_alias=AliasPath("addresses", 1, "city"))


order = OrderSchema.model_validate({"ORDER_ID": 7})
assert order.model_dump(by_alias=True) == {"orderId": 7}

payload = {
    "ID": 5,
    "customer_id": 9,
    "addresses": [{"city": "Recife"}, {"city": "Teresina"}],
}
customer = CustomerSchema.model_validate(payload)
assert customer.customer_id == 9
assert customer.city == "Teresina"

print(order.model_dump(by_alias=True))
print(customer)
