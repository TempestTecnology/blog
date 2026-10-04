"""`include` e `exclude` com set, dict aninhado, `__all__` e índice de lista."""

from pydantic import BaseModel, Field


class ItemSchema(BaseModel):
    """Item de um pedido."""

    sku: str
    qty: int
    cost: int = Field(default=0, exclude=True)


class OrderSchema(BaseModel):
    """Pedido com lista de itens."""

    id: int
    note: str
    items: list[ItemSchema]


order = OrderSchema(
    id=1,
    note="entregar à tarde",
    items=[ItemSchema(sku="A", qty=1, cost=5), ItemSchema(sku="B", qty=2, cost=7)],
)

only_ids = order.model_dump(include={"id": True, "items": {"__all__": {"sku"}}})
first_item = order.model_dump(include={"items": {0: {"sku"}}})
without_qty = order.model_dump(exclude={"note": True, "items": {"__all__": {"qty"}}})
exclude_wins = order.model_dump(include={"id", "note"}, exclude={"note"})
field_exclude_wins = order.model_dump(include={"items": {"__all__": {"sku", "cost"}}})

print(only_ids, first_item, without_qty, exclude_wins, field_exclude_wins, sep="\n")

assert only_ids == {"id": 1, "items": [{"sku": "A"}, {"sku": "B"}]}
assert first_item == {"items": [{"sku": "A"}]}
assert without_qty == {"id": 1, "items": [{"sku": "A"}, {"sku": "B"}]}
assert exclude_wins == {"id": 1}
assert field_exclude_wins == {"items": [{"sku": "A"}, {"sku": "B"}]}
assert order.model_dump(include={"does_not_exist"}) == {}
