"""`warnings` decide o barulho de valor fora do tipo; `fallback` serializa o desconhecido."""

import warnings as py_warnings
from typing import Any

from pydantic import BaseModel, ConfigDict
from pydantic_core import PydanticSerializationError


class CounterSchema(BaseModel):
    """Contador inteiro."""

    total: int


broken = CounterSchema.model_construct(total="oops")

with py_warnings.catch_warnings(record=True) as caught:
    py_warnings.simplefilter("always")
    print(broken.model_dump())
    assert len(caught) == 1

with py_warnings.catch_warnings(record=True) as caught:
    py_warnings.simplefilter("always")
    broken.model_dump(warnings=False)
    assert caught == []

try:
    broken.model_dump(warnings="error")
except PydanticSerializationError as error:
    print("warnings='error':", str(error).splitlines()[1].strip()[:60])


class Coordinate:
    """Classe comum, sem nada de Pydantic."""

    def __init__(self, lat: float, lng: float) -> None:
        """Guarda latitude e longitude.

        Args:
            lat (float): Latitude.
            lng (float): Longitude.
        """
        self.lat: float = lat
        self.lng: float = lng


class PlaceSchema(BaseModel):
    """Lugar com um campo de tipo arbitrário."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    location: Any


place = PlaceSchema(location=Coordinate(-5.09, -42.80))

try:
    place.model_dump(mode="json")
except PydanticSerializationError as error:
    print("sem fallback:", error)

as_json = place.model_dump(mode="json", fallback=vars)
print(as_json)
assert as_json == {"location": {"lat": -5.09, "lng": -42.80}}
