"""O estado de uma instância: campos setados, extras, privados, `==` e `hash`."""

from typing import Any

from pydantic import BaseModel, ConfigDict, PrivateAttr


class EventSchema(BaseModel):
    """Evento que aceita chaves extras e tem um cache privado."""

    model_config = ConfigDict(extra="allow")

    id: int
    source: str = "api"
    _cache: dict[str, Any] = PrivateAttr(default_factory=dict)


event = EventSchema.model_validate({"id": 1, "trace_id": "abc"})
print("model_fields_set:", event.model_fields_set)
print("model_extra:", event.model_extra)
print("__pydantic_private__:", event.__pydantic_private__)
print("iter:", list(event))

assert event.model_fields_set == {"id", "trace_id"}
assert event.model_extra == {"trace_id": "abc"}
assert event.model_fields_set is event.__pydantic_fields_set__
assert "_cache" not in event.model_dump()

twin = EventSchema.model_validate({"id": 1, "trace_id": "abc"})
assert event == twin
twin._cache["hit"] = True
print("== depois de mexer no cache:", event == twin)
assert event != twin

try:
    hash(event)
except TypeError as error:
    print("hash:", error)
