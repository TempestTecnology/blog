"""Com alias, o nome do campo deixa de valer na entrada — e o `extra` decide o barulho."""

from pydantic import ConfigDict, Field
from tempest_fastapi_sdk import BaseSchema


class PageFilterSchema(BaseSchema):
    """`BaseSchema` traz `extra="ignore"`: chave desconhecida some em silêncio."""

    page_size: int = Field(default=20, alias="pageSize")


class PageFilterByNameSchema(BaseSchema):
    """Aceita o alias e o nome do campo na entrada."""

    model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)

    page_size: int = Field(default=20, alias="pageSize")


silent = PageFilterSchema.model_validate({"page_size": 100})
print("sem validate_by_name:", silent)
assert silent.page_size == 20

by_name = PageFilterByNameSchema.model_validate({"page_size": 100})
by_alias = PageFilterByNameSchema.model_validate({"pageSize": 50})
print("com validate_by_name:", by_name, "|", by_alias)
assert by_name.page_size == 100
assert by_alias.page_size == 50
