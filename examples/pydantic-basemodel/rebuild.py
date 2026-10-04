"""Forward reference, `__pydantic_complete__` e `model_rebuild`."""

from pydantic import BaseModel
from pydantic.errors import PydanticUserError


class CategorySchema(BaseModel):
    """Categoria que referencia um tipo ainda não definido."""

    name: str
    parent: "ParentSchema | None" = None


print("completo antes:", CategorySchema.__pydantic_complete__)
try:
    CategorySchema(name="Bebidas")
except PydanticUserError as error:
    print("instanciar antes:", error.code)


class ParentSchema(BaseModel):
    """O tipo que faltava."""

    name: str


print("rebuild:", CategorySchema.model_rebuild())
print("completo depois:", CategorySchema.__pydantic_complete__)
print("rebuild de novo:", CategorySchema.model_rebuild())
print(CategorySchema(name="Cafés", parent={"name": "Bebidas"}))
