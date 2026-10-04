"""`union_mode` e `fail_fast`."""

from pydantic import BaseModel, Field, ValidationError


class UnionSchema(BaseModel):
    """A mesma união `int | str`, em dois modos."""

    smart: int | str
    left_to_right: int | str = Field(union_mode="left_to_right")


result = UnionSchema(smart="1", left_to_right="1")
print(result)
assert result.smart == "1"
assert result.left_to_right == 1


class BatchSchema(BaseModel):
    """Lote de ids, com e sem `fail_fast`."""

    fast: list[int] = Field(fail_fast=True)
    full: list[int]


try:
    BatchSchema(fast=["a", "b", "c"], full=["a", "b", "c"])
except ValidationError as error:
    print([item["loc"] for item in error.errors()])
