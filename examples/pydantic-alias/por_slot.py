"""A trava do gerador protege o que você escreveu, não o campo inteiro."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class InvoiceSchema(BaseModel):
    """Só `validation_alias` declarado; os outros dois slots ficam vazios."""

    model_config = ConfigDict(alias_generator=to_camel)

    due_date: str = Field(validation_alias="VENCIMENTO")


field = InvoiceSchema.model_fields["due_date"]
print(f"alias={field.alias!r}")
print(f"validation_alias={field.validation_alias!r}")
print(f"serialization_alias={field.serialization_alias!r}")
print(f"alias_priority={field.alias_priority}")

assert field.alias_priority == 2
assert field.validation_alias == "VENCIMENTO"
assert field.alias == "dueDate"
assert field.serialization_alias == "dueDate"

invoice = InvoiceSchema.model_validate({"VENCIMENTO": "2026-10-04"})
assert invoice.model_dump(by_alias=True) == {"dueDate": "2026-10-04"}
