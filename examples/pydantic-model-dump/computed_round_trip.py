"""`exclude_computed_fields` e `round_trip`: o dump que volta a ser entrada."""

from pydantic import BaseModel, ConfigDict, Json, ValidationError, computed_field


class RectangleSchema(BaseModel):
    """Retângulo com área calculada; `extra="forbid"` recusa chave a mais."""

    model_config = ConfigDict(extra="forbid")

    width: int
    height: int

    @computed_field
    @property
    def area(self) -> int:
        """Área do retângulo.

        Returns:
            Largura vezes altura.
        """
        return self.width * self.height


rectangle = RectangleSchema(width=2, height=3)
print(rectangle.model_dump(), rectangle.model_dump(exclude_computed_fields=True))
assert rectangle.model_dump() == {"width": 2, "height": 3, "area": 6}

try:
    RectangleSchema.model_validate(rectangle.model_dump())
except ValidationError as error:
    print("recusou o próprio dump:", error.errors()[0]["type"])

assert RectangleSchema.model_validate(rectangle.model_dump(exclude_computed_fields=True)) == rectangle
assert rectangle.model_dump(round_trip=True) == {"width": 2, "height": 3}


class WebhookSchema(BaseModel):
    """Payload que chega como string JSON."""

    payload: Json[dict[str, int]]


webhook = WebhookSchema(payload='{"attempt": 1}')
print(webhook.model_dump(), webhook.model_dump(round_trip=True))
assert webhook.model_dump() == {"payload": {"attempt": 1}}
assert webhook.model_dump(round_trip=True) == {"payload": '{"attempt":1}'}
assert WebhookSchema.model_validate(webhook.model_dump(round_trip=True)) == webhook

try:
    WebhookSchema.model_validate(webhook.model_dump())
except ValidationError as error:
    print("sem round_trip:", error.errors()[0]["type"])
