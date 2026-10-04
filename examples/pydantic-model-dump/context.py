"""`context` chega no serializer customizado via `SerializationInfo`."""

from typing import Any

from pydantic import BaseModel, SerializationInfo, field_serializer


class PriceSchema(BaseModel):
    """Preço guardado em centavos."""

    cents: int

    @field_serializer("cents")
    def serialize_cents(self, value: int, info: SerializationInfo) -> Any:
        """Formata em reais quando o contexto pede.

        Args:
            value (int): Valor em centavos.
            info (SerializationInfo): Metadados da chamada, com o `context`.

        Returns:
            O inteiro original, ou o texto `R$ x,yy` com `as_reais` no contexto.
        """
        if info.context and info.context.get("as_reais"):
            return f"R$ {value / 100:.2f}".replace(".", ",")
        return value


price = PriceSchema(cents=990)
print(price.model_dump(), price.model_dump(context={"as_reais": True}))

assert price.model_dump() == {"cents": 990}
assert price.model_dump(context={"as_reais": True}) == {"cents": "R$ 9,90"}
