"""`mode` escolhe entre objetos Python e tipos que cabem em JSON."""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class Status(Enum):
    """Status de um pedido."""

    PAID = "paid"


class PaymentSchema(BaseModel):
    """Pagamento com tipos que o JSON não conhece."""

    id: UUID
    paid_at: datetime
    amount: Decimal
    tags: set[str]
    status: Status


payment = PaymentSchema(
    id=UUID(int=1),
    paid_at=datetime(2026, 10, 4, 10, 0),
    amount=Decimal("9.90"),
    tags={"pix"},
    status=Status.PAID,
)

as_python = payment.model_dump()
as_json = payment.model_dump(mode="json")
print(as_python)
print(as_json)

assert isinstance(as_python["id"], UUID)
assert as_json == {
    "id": "00000000-0000-0000-0000-000000000001",
    "paid_at": "2026-10-04T10:00:00",
    "amount": "9.90",
    "tags": ["pix"],
    "status": "paid",
}
assert payment.model_dump(mode="JSON") == as_python
