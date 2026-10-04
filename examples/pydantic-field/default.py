"""`default`, `default_factory` e `validate_default`."""

from pydantic import BaseModel, Field, ValidationError


class AccountSchema(BaseModel):
    """Conta com default mutável, factory e factory que lê outro campo."""

    first_name: str
    roles: list[str] = []
    tags: list[str] = Field(default_factory=list)
    slug: str = Field(default_factory=lambda data: data["first_name"].lower())


ana = AccountSchema(first_name="Ana")
bia = AccountSchema(first_name="Bia")
ana.roles.append("admin")
print(ana, bia, sep="\n")

assert bia.roles == []
assert ana.slug == "ana"


class TrustedDefaultSchema(BaseModel):
    """Default errado, aceito sem validação."""

    retries: int = "três"


class CheckedDefaultSchema(BaseModel):
    """`validate_default=True` valida (e converte) o default."""

    retries: int = Field(default="3", validate_default=True)


print(TrustedDefaultSchema(), CheckedDefaultSchema())
assert TrustedDefaultSchema().retries == "três"
assert CheckedDefaultSchema().retries == 3

try:

    class BothSchema(BaseModel):
        """Os dois ao mesmo tempo."""

        tags: list[str] = Field(default=[], default_factory=list)

except TypeError as error:
    print("default + default_factory:", error)


class WrongOrderSchema(BaseModel):
    """A factory lê um campo que ainda não foi validado."""

    slug: str = Field(default_factory=lambda data: data["first_name"].lower())
    first_name: str


try:
    WrongOrderSchema(first_name="Ana")
except KeyError as error:
    print("factory antes do campo que ela lê: KeyError", error)
