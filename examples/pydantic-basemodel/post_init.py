"""`model_post_init` roda depois da validação e recebe o `context`."""

from typing import Any

from pydantic import BaseModel, PrivateAttr


class RequestSchema(BaseModel):
    """Payload que guarda, fora dos campos, quem o validou."""

    amount: int
    _tenant: str | None = PrivateAttr(default=None)

    def model_post_init(self, context: Any, /) -> None:
        """Lê o tenant do contexto de validação.

        Args:
            context (Any): O `context` passado ao `model_validate`, ou `None`.
        """
        if isinstance(context, dict):
            self._tenant = context.get("tenant")


with_context = RequestSchema.model_validate({"amount": 10}, context={"tenant": "acme"})
without_context = RequestSchema(amount=10)
print(with_context._tenant, without_context._tenant)

assert with_context._tenant == "acme"
assert without_context._tenant is None
assert with_context.model_dump() == {"amount": 10}
