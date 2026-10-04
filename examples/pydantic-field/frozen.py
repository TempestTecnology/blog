"""`frozen=True` bloqueia atribuição — mas não o `model_copy(update=...)`."""

from pydantic import BaseModel, Field, ValidationError


class InvoiceSchema(BaseModel):
    """Fatura com id imutável."""

    id: int = Field(frozen=True)
    status: str


invoice = InvoiceSchema(id=1, status="open")

try:
    invoice.id = 2
except ValidationError as error:
    print("atribuição:", error.errors()[0]["type"])

copied = invoice.model_copy(update={"id": 999})
print("model_copy:", copied)
assert copied.id == 999

try:
    hash(invoice)
except TypeError as error:
    print("hash:", error)
