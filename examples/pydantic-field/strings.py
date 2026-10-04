"""`pattern`, tamanho, `strict` e `coerce_numbers_to_str`."""

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from pydantic_core import SchemaError


class CodeSchema(BaseModel):
    """`pattern` sem e com âncoras."""

    loose: str = Field(pattern=r"\d{3}")
    anchored: str = Field(pattern=r"^\d{3}$")


print(CodeSchema(loose="abc123xyz", anchored="123"))

try:
    CodeSchema(loose="123", anchored="abc123xyz")
except ValidationError as error:
    print("ancorado:", error.errors()[0]["type"])

try:

    class LookaheadSchema(BaseModel):
        """Lookahead no motor padrão (Rust)."""

        password: str = Field(pattern=r"^(?=.*\d).{8,}$")

except SchemaError:
    print("lookahead no motor Rust: SchemaError na definição da classe")


class PythonRegexSchema(BaseModel):
    """`regex_engine="python-re"` aceita lookahead."""

    model_config = ConfigDict(regex_engine="python-re")

    password: str = Field(pattern=r"^(?=.*\d).{8,}$")


print(PythonRegexSchema(password="segredo1"))


class LengthSchema(BaseModel):
    """`max_length` conta depois do `str_strip_whitespace`."""

    model_config = ConfigDict(str_strip_whitespace=True)

    uf: str = Field(min_length=2, max_length=2)
    items: list[int] = Field(min_length=1)


print(LengthSchema(uf="  PI  ", items=[1]))


class StrictSchema(BaseModel):
    """`strict` recusa conversão; `coerce_numbers_to_str` aceita número em `str`."""

    quantity: int = Field(strict=True)
    document: str = Field(coerce_numbers_to_str=True)


print(StrictSchema(quantity=1, document=12345678900))
assert StrictSchema(quantity=1, document=123).document == "123"

for value in ("1", 1.0):
    try:
        StrictSchema(quantity=value, document="x")
    except ValidationError as error:
        print(f"strict com {value!r}:", error.errors()[0]["type"])
