---
date:
  created: 2026-10-04 13:00:00
authors:
  - mauricio
categories:
  - tempest-fastapi-sdk
  - Python
tags:
  - pydantic
  - fastapi
slug: pydantic-basemodel
---

# Tudo do `BaseModel`: métodos, estado e o que mora nos `__dunders__`

Todo schema do `tempest-fastapi-sdk` herda de `BaseModel`. Você usa
`model_validate` e `model_dump` todo dia — mas a classe tem **16 membros
`model_*`**, uma dúzia de atributos `__pydantic_*__` e 12 métodos da v1 ainda
de pé. Este post passa por todos, com as surpresas: um `==` que compara
atributo privado, um `model_copy` que ignora alias em silêncio e um
`model_construct` que pula até o seu `__init__`.

<!-- more -->

Fecha a série com [`alias`](2026-10-04-pydantic-alias.md),
[`model_dump()`](2026-10-04-pydantic-model-dump.md) e
[`Field()`](2026-10-04-pydantic-field.md). Todo exemplo roda na CI do blog. ✅

!!! info "Versões"
    Medido com **Pydantic 2.13.5**.

## Mapa rápido

| Pergunta | Membros |
| --- | --- |
| Como **crio** uma instância? | `model_validate`, `model_validate_json`, `model_validate_strings`, `model_construct` |
| E depois de validar? | `model_post_init` |
| Como **copio**? | `model_copy` |
| Como **serializo**? | `model_dump`, `model_dump_json` ([post próprio](2026-10-04-pydantic-model-dump.md)) |
| Que **estado** a instância carrega? | `model_fields_set`, `model_extra`, `__pydantic_fields_set__`, `__pydantic_extra__`, `__pydantic_private__` |
| O que a **classe** sabe de si? | `model_config`, `model_fields`, `model_computed_fields`, `__class_vars__`, `__private_attributes__`, `__signature__`, `__pydantic_decorators__`, `__pydantic_post_init__`, `__pydantic_custom_init__`, `__pydantic_root_model__` |
| E a **forward reference**? | `model_rebuild`, `__pydantic_complete__`, `__pydantic_parent_namespace__` |
| E **genéricos**? | `model_parametrized_name`, `__pydantic_generic_metadata__` |
| O que tem **por baixo**? | `__pydantic_core_schema__`, `__pydantic_validator__`, `__pydantic_serializer__`, `model_json_schema` |
| **Ganchos** de subclasse? | `__pydantic_init_subclass__`, `__pydantic_on_complete__` |

## Criar: as três portas de entrada

```python title="examples/pydantic-basemodel/validar.py"
--8<-- "pydantic-basemodel/validar.py"
```

Saída:

```text
id=1 name='Ana' born=None
id=1 name='Ana' born=None
id=1 name='Ana' born=None
id=1 name='Ana' born=datetime.date(2000, 1, 31)
id=1 name='Ana' born=datetime.date(2000, 1, 31)
strict=True, id='1'          int_type
extra='forbid' na chamada    extra_forbidden
objeto sem from_attributes   model_type
strict, data como str        date_type
validate_strings com int     string_type
```

- **`model_validate(obj)`** — entrada é objeto Python (`dict`, ou objeto
  com atributos se `from_attributes=True`).
- **`model_validate_json(data)`** — entrada é `str`/`bytes` de JSON. Parseia
  e valida numa passada só, em Rust: mais rápido que
  `model_validate(json.loads(data))`.
- **`model_validate_strings(obj)`** — entrada é um `dict` em que **todo
  valor é string**, como query string, form ou variável de ambiente. Mesmo
  com `strict=True`, `"2000-01-31"` vira `date`; um valor que não é `str`
  dá `string_type`.

Os três aceitam, **por chamada**, o que normalmente mora no
`model_config`: `strict`, `extra`, `from_attributes` (só no
`model_validate`), `context`, `by_alias` e `by_name`. O `extra="forbid"` do
exemplo vale só naquela chamada, sem mexer no model.

!!! tip "No `tempest-fastapi-sdk`"
    O `BaseSchema` já liga `from_attributes=True` no `model_config`. Por isso
    um model SQLAlchemy entra direto no `model_validate`, sem flag.

## `model_construct`: sem validação nenhuma

```python title="examples/pydantic-basemodel/construct.py"
--8<-- "pydantic-basemodel/construct.py"
```

Saída:

```text
id='não é int' name='  Ana  ' tags=[] {'name', 'id'} []
```

`model_construct` monta a instância **confiando** nos dados: aceita alias,
preenche defaults e calcula `model_fields_set` — mas não converte tipo, não
roda validator e **não chama o seu `__init__`**. O `model_validate` e o
`model_validate_json`, ao contrário, chamam o `__init__` customizado
(`CALLS` termina com dois registros).

`_fields_set` deixa você dizer quais campos contam como "setados" — útil
para reconstruir um PATCH a partir do banco.

!!! danger "Só para dado que já foi validado"
    Use para reidratar o que **você mesmo** serializou (cache, banco, fila).
    Nunca para entrada de usuário: um `id` que é string passa direto e
    estoura lá na frente.

## `model_post_init`: depois da validação

```python title="examples/pydantic-basemodel/post_init.py"
--8<-- "pydantic-basemodel/post_init.py"
```

Saída:

```text
acme None
```

Roda **depois** que todos os campos foram validados, então você já tem a
instância inteira. Recebe o `context` do `model_validate(..., context=...)`
— e `None` quando a instância vem do construtor, que não aceita `context`.
Lugar natural para inicializar `PrivateAttr`.

## `model_copy`: rasa, e o `update` não valida

```python title="examples/pydantic-basemodel/copiar.py"
--8<-- "pydantic-basemodel/copiar.py"
```

Saída:

```text
cópia rasa: ['a', 'b']
update sem validação: 'não é int'
update por alias: Ana {'id': 1, 'name': 'Ana', 'tags': ['a', 'b']}
```

Três armadilhas numa função só:

1. **Cópia rasa por padrão**: a lista é a mesma nas duas instâncias — o
   `append` na cópia aparece no original. `deep=True` resolve.
2. **`update` não valida**: `id="não é int"` entra como está.
3. **`update` usa nome de campo, não alias**: `update={"fullName": "Bia"}`
   não muda `name`. Vira um atributo solto, que não aparece no dump. Nenhum
   erro.

!!! tip "Precisa validar a mudança?"
    `Model.model_validate({**obj.model_dump(), "id": novo_id})` valida tudo
    de novo. Mais caro, mas é o caminho seguro para dado que veio de fora.

## Estado da instância

```python title="examples/pydantic-basemodel/estado.py"
--8<-- "pydantic-basemodel/estado.py"
```

Saída:

```text
model_fields_set: {'trace_id', 'id'}
model_extra: {'trace_id': 'abc'}
__pydantic_private__: {'_cache': {}}
iter: [('id', 1), ('source', 'api'), ('trace_id', 'abc')]
== depois de mexer no cache: False
hash: unhashable type: 'EventSchema'
```

- **`model_fields_set`** (o mesmo objeto que `__pydantic_fields_set__`):
  campos passados na entrada ou atribuídos depois. **Inclui as chaves
  extras** quando `extra="allow"` — `trace_id` está lá.
- **`model_extra`** (`__pydantic_extra__`): as chaves extras. É `None`
  quando `extra` não é `"allow"`.
- **`__pydantic_private__`**: os valores dos `PrivateAttr`. Nunca saem no
  `model_dump`.
- **`iter(obj)`** devolve pares `(campo, valor)`, extras incluídos, computed
  fields não.

!!! warning "`==` compara os atributos privados"
    Duas instâncias com os mesmos campos são iguais — até alguém mexer num
    `PrivateAttr`. Aí `==` vira `False`. Se o privado é cache, compare
    `a.model_dump() == b.model_dump()`.

E `hash()` falha: model é mutável por padrão. Para hashear, é
`model_config = ConfigDict(frozen=True)`.

## O que a classe sabe de si

```python title="examples/pydantic-basemodel/classe.py"
--8<-- "pydantic-basemodel/classe.py"
```

Saída:

```text
model_fields: ['sku', 'name', 'cents']
model_computed_fields: ['price']
__class_vars__: {'currency'}
__private_attributes__: ['_views']
__signature__: (*, sku: str, displayName: str, cents: int = 0) -> None
field_validators: ['upper_sku']
__pydantic_post_init__: model_post_init
__pydantic_custom_init__: False
__pydantic_root_model__: False True
model_fields na instância: PydanticDeprecatedSince211
```

| Atributo | O que guarda |
| --- | --- |
| `model_config` | a `ConfigDict` do model, já mesclada com a das bases |
| `model_fields` / `__pydantic_fields__` | `FieldInfo` de cada campo (o mesmo objeto) |
| `model_computed_fields` / `__pydantic_computed_fields__` | `ComputedFieldInfo` de cada `@computed_field` |
| `__class_vars__` | nomes declarados como `ClassVar` — não são campos |
| `__private_attributes__` | a declaração de cada `PrivateAttr` (o valor fica em `__pydantic_private__`) |
| `__signature__` | a assinatura do `__init__` — com **alias**, não nome de campo |
| `__pydantic_decorators__` | `field_validators`, `model_validators`, `field_serializers`… (substitui `__validators__` da v1) |
| `__pydantic_post_init__` | `"model_post_init"` se existe, senão `None` |
| `__pydantic_custom_init__` | `True` se você sobrescreveu `__init__` — é o que faz a validação chamá-lo |
| `__pydantic_root_model__` | `True` em `RootModel` |

!!! warning "`model_fields` é da classe"
    Desde o 2.11, ler `obj.model_fields` na **instância** emite
    `PydanticDeprecatedSince211`. Use `type(obj).model_fields`.

## Forward reference: `model_rebuild`

```python title="examples/pydantic-basemodel/rebuild.py"
--8<-- "pydantic-basemodel/rebuild.py"
```

Saída:

```text
completo antes: False
instanciar antes: class-not-fully-defined
rebuild: True
completo depois: True
rebuild de novo: None
```

Quando uma anotação cita um tipo que ainda não existe, a classe nasce
**incompleta** (`__pydantic_complete__ = False`) e não valida. O Pydantic
tenta completar sozinho no primeiro uso; `model_rebuild()` força. O retorno
diz o que aconteceu:

- `True` — reconstruiu agora.
- `None` — já estava completo, nada a fazer (`force=True` reconstrói assim
  mesmo).
- `False` — não conseguiu, com `raise_errors=False`. Com o padrão
  `raise_errors=True`, é `PydanticUndefinedAnnotation`.

`__pydantic_parent_namespace__` guarda o namespace onde a classe foi
definida, para esse rebuild achar nomes locais. Em classe de nível de
módulo é `None` — o módulo já basta; em classe definida dentro de função, é
um `dict`.

## Genéricos

```python title="examples/pydantic-basemodel/genericos.py"
--8<-- "pydantic-basemodel/genericos.py"
```

Saída:

```text
PageSchema[int] IntPage
{'origin': None, 'args': (), 'parameters': (~T,)}
{'origin': <class '__main__.PageSchema'>, 'args': (<class 'int'>,), 'parameters': ()}
IntPage
items=[1, 2]
```

- **`__pydantic_generic_metadata__`**: na classe genérica, os
  `parameters` (`T`); na parametrizada, a `origin` e os `args` (`int`).
- **`model_parametrized_name`**: sobrescreva para trocar o nome da classe
  parametrizada. Esse nome vira o `title` do JSON Schema — e o nome do
  schema no Swagger. `IntPage` lê melhor que `PageSchema[int]`.

## Por baixo: core schema, validator e serializer

```python title="examples/pydantic-basemodel/core.py"
--8<-- "pydantic-basemodel/core.py"
```

Saída:

```text
model
SchemaValidator SchemaSerializer
user_id=1 {'user_id': 1}
model_dump(): {'user_id': 1}
model_json_schema(): ['userId']
```

- **`__pydantic_core_schema__`**: a descrição do model que o
  `pydantic-core` (Rust) entende.
- **`__pydantic_validator__`** / **`__pydantic_serializer__`**: o
  `SchemaValidator` e o `SchemaSerializer` compilados a partir dele. Todo
  `model_validate` e `model_dump` termina aqui.

!!! warning "Os defaults de `by_alias` discordam"
    `model_dump()` usa **nome de campo** por padrão; `model_json_schema()`
    usa **alias**. O schema documenta `userId` e o dump devolve `user_id`. No
    FastAPI os dois batem porque o `response_model` serializa com
    `by_alias=True` — fora dele, passe `by_alias=True` no dump.

## Ganchos de subclasse

```python title="examples/pydantic-basemodel/ganchos.py"
--8<-- "pydantic-basemodel/ganchos.py"
```

Saída:

```text
['on_complete:RegisteredSchema', 'on_complete:OrderSchema', 'init_subclass:OrderSchema', 'init_subclass:ShipmentSchema']
[..., 'on_complete:ShipmentSchema']
```

Prefira estes ao `__init_subclass__` do Python, que roda **antes** de o
Pydantic montar os campos.

- **`__pydantic_init_subclass__`** roda logo depois da criação da classe —
  **mesmo incompleta**: `ShipmentSchema` aparece aqui antes do
  `AddressSchema` existir.
- **`__pydantic_on_complete__`** roda quando a classe **está pronta para
  validar**: na criação, ou só depois do `model_rebuild()`.

Para um registry que precisa validar (gerar schema, instanciar exemplo),
`__pydantic_on_complete__` é o gancho certo.

## A API da v1

Ainda funciona, com `PydanticDeprecatedSince20`. Sai na v3:

| v1 | v2 |
| --- | --- |
| `obj.dict()` | `obj.model_dump()` |
| `obj.json()` | `obj.model_dump_json()` |
| `obj.copy()` | `obj.model_copy()` |
| `Model.parse_obj(d)` / `Model.validate(d)` | `Model.model_validate(d)` |
| `Model.parse_raw(s)` / `Model.parse_file(p)` | `Model.model_validate_json(...)` |
| `Model.from_orm(o)` | `Model.model_validate(o, from_attributes=True)` |
| `Model.construct(...)` | `Model.model_construct(...)` |
| `Model.schema()` / `Model.schema_json()` | `Model.model_json_schema()` |
| `Model.update_forward_refs()` | `Model.model_rebuild()` |

!!! note "`from_orm` não é só um alias"
    `Model.from_orm(o)` exige `from_attributes=True` no `model_config` —
    sem isso, `PydanticUserError`. O `model_validate` aceita a flag por
    chamada.

## Recap

- **Entrada**: `model_validate` (objeto), `model_validate_json` (JSON, mais
  rápido), `model_validate_strings` (tudo string). Todos aceitam `strict`,
  `extra`, `context`, `by_alias`, `by_name` por chamada.
- **`model_construct`** pula validação, validators **e** o `__init__`
  customizado — só para dado já validado.
- **`model_post_init`** roda depois da validação e recebe o `context`.
- **`model_copy`** é rasa, o `update` não valida e **ignora alias em
  silêncio**.
- **`model_fields_set` inclui chaves extras**; `model_extra` é `None` sem
  `extra="allow"`.
- **`==` compara `PrivateAttr`**; `hash` só com `frozen=True`.
- **`model_fields` é da classe** — na instância, deprecado desde o 2.11.
- **`model_dump()` usa nome de campo; `model_json_schema()` usa alias.**
- **`__pydantic_on_complete__`** espera a classe ficar pronta;
  **`__pydantic_init_subclass__`** não. 🚀
