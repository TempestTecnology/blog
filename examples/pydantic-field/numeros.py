"""Limites numéricos, `allow_inf_nan`, `Decimal` e constraint no tipo errado."""

from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError


class ScoreSchema(BaseModel):
    """Nota, temperatura e preço."""

    score: float = Field(ge=0, le=10, multiple_of=0.5)
    temperature: float = 0
    safe_temperature: float = Field(default=0, allow_inf_nan=False)
    price: Decimal = Field(default=Decimal("0"), max_digits=5, decimal_places=2)


hot = ScoreSchema(score=9.5, temperature="inf")
print(hot)
print(hot.model_dump_json())
assert '"temperature":null' in hot.model_dump_json()

attempts = {
    "score=11": {"score": 11},
    "score=7.3": {"score": 7.3},
    "score=nan": {"score": "nan"},
    "safe_temperature=inf": {"score": 1, "safe_temperature": "inf"},
    "price=1234.5": {"score": 1, "price": "1234.5"},
    "price=1.234": {"score": 1, "price": "1.234"},
}
for label, data in attempts.items():
    try:
        ScoreSchema(**data)
    except ValidationError as error:
        print(f"{label:22}", error.errors()[0]["type"])

print(ScoreSchema(score=1, price="1.2300"))


class WrongTypeSchema(BaseModel):
    """`max_digits` num `str`: a classe é criada sem erro."""

    code: str = Field(max_digits=3)


try:
    WrongTypeSchema(code="12345")
except ValidationError:
    print("ValidationError")
except TypeError as error:
    print("TypeError, não ValidationError:", error)
