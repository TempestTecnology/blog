---
date:
  created: 2026-10-04 11:00:00
authors:
  - mauricio
categories:
  - tempest-fastapi-sdk
  - Python
tags:
  - pydantic
  - fastapi
  - serialização
slug: pydantic-model-dump
---

# Todos os parâmetros do `model_dump()`

`model_dump()` tem **14 parâmetros**, e quase todo mundo usa dois. Os outros
doze resolvem problemas reais — e alguns escondem armadilhas: um `mode` que
aceita qualquer string, um `exclude_unset` que não vê `.append()` e um
`serialize_as_any` que pode vazar `password_hash` na resposta da API.

<!-- more -->

Como no [post sobre `alias`](2026-10-04-pydantic-alias.md), todo exemplo é um script
com `assert` que roda na CI do blog. ✅

!!! info "Versões"
    Medido com **Pydantic 2.13.5** e **tempest-fastapi-sdk 0.303.0**.

## Mapa rápido

| Pergunta | Parâmetros |
| --- | --- |
| Que **tipos** saem? | `mode` |
| Que **campos** saem? | `include`, `exclude`, `exclude_unset`, `exclude_defaults`, `exclude_none`, `exclude_computed_fields` |
| Com que **nome**? | `by_alias` |
| O dump **volta** a ser entrada? | `round_trip` |
| O que o **serializer customizado** recebe? | `context` |
| E quando um valor **não serializa**? | `warnings`, `fallback` |
| E **subclasses**? | `serialize_as_any`, `polymorphic_serialization` |

!!! tip "`model_dump_json()`"
    Aceita os mesmos parâmetros, menos `mode` (é sempre JSON), e soma
    `indent` e `ensure_ascii`. Tudo deste post vale para os dois.

## `mode`: objetos Python ou tipos JSON

```python title="examples/pydantic-model-dump/mode.py"
--8<-- "pydantic-model-dump/mode.py"
```

Saída:

```text
{'id': UUID('00000000-0000-0000-0000-000000000001'), 'paid_at': datetime.datetime(2026, 10, 4, 10, 0), 'amount': Decimal('9.90'), 'tags': {'pix'}, 'status': <Status.PAID: 'paid'>}
{'id': '00000000-0000-0000-0000-000000000001', 'paid_at': '2026-10-04T10:00:00', 'amount': '9.90', 'tags': ['pix'], 'status': 'paid'}
```

- `mode="python"` (padrão) devolve os objetos como estão: `UUID`,
  `datetime`, `Decimal`, `set`, `Enum`.
- `mode="json"` devolve só o que cabe em JSON: `str`, `int`, `float`,
  `bool`, `None`, `list`, `dict`. É o que você quer antes de mandar para
  `json.dumps`, uma coluna `JSONB`, Redis ou uma fila.

!!! danger "Qualquer string que não seja `"json"` vira `"python"`"
    O tipo é `str`, e nada é validado: `mode="JSON"` (maiúsculo) ou um typo
    rodam **sem erro** e devolvem objetos Python. O erro só aparece lá na
    frente, quando o `json.dumps` engasga com um `UUID`. A última linha do
    exemplo prova isso.

## `include` e `exclude`: que campos saem

Aceitam `set` (só nomes) ou `dict` (para descer em campos aninhados):

```python title="examples/pydantic-model-dump/include_exclude.py" hl_lines="28 29 30 31 32"
--8<-- "pydantic-model-dump/include_exclude.py"
```

Saída:

```text
{'id': 1, 'items': [{'sku': 'A'}, {'sku': 'B'}]}
{'items': [{'sku': 'A'}]}
{'id': 1, 'items': [{'sku': 'A'}, {'sku': 'B'}]}
{'id': 1}
{'items': [{'sku': 'A'}, {'sku': 'B'}]}
```

As regras:

- **`dict` desce na estrutura**: `{"items": {"__all__": {"sku"}}}` aplica a
  todo item da lista; `{"items": {0: {"sku"}}}`, só ao índice `0`.
- **`True` num dict** quer dizer "o campo inteiro": `{"id": True, ...}`.
- **`exclude` ganha de `include`** quando os dois citam o mesmo campo.
- **`Field(exclude=True)` ganha de tudo**: `cost` não sai nem pedindo no
  `include`.
- **Nome que não existe é ignorado em silêncio** — `include={"nome_errado"}`
  devolve `{}`, sem erro.

## `context`: dado extra para o serializer customizado

`context` não muda nada sozinho. Ele chega em `info.context` dentro de um
`@field_serializer` ou `@model_serializer`, e o serializer decide o que
fazer:

```python title="examples/pydantic-model-dump/context.py" hl_lines="24 25"
--8<-- "pydantic-model-dump/context.py"
```

Saída:

```text
{'cents': 990} {'cents': 'R$ 9,90'}
```

Bom para variar a saída por chamada (locale, nível de permissão, versão da
API) sem criar um schema para cada caso.

## `by_alias`: com que nome

```python title="examples/pydantic-model-dump/by_alias.py"
--8<-- "pydantic-model-dump/by_alias.py"
```

Saída:

```text
{'user_id': 1} {'userId': 1}
{'userId': 1} {'user_id': 1}
```

O padrão é `None`, não `False`: `None` quer dizer "siga o
`serialize_by_alias` do `model_config`" (que é `False` se ninguém mexer). Um
`True` ou `False` explícito na chamada ganha da config.

!!! note "Qual alias?"
    O dump usa o `serialization_alias` — ou o `alias`, que preenche os dois
    lados. Detalhes no [post sobre os três `alias`](2026-10-04-pydantic-alias.md).

## `exclude_unset`: só o que alguém passou

`exclude_unset=True` mantém só os campos que estão em `model_fields_set` —
os que vieram na entrada ou foram atribuídos depois. É o parâmetro do
**PATCH**: atualizar só o que o cliente mandou.

E é aqui que o `tempest-fastapi-sdk` entra. O `BaseSchema.to_dict()` é, por
dentro:

```python
self.model_dump(exclude_none=True, exclude_unset=True)
```

```python title="examples/pydantic-model-dump/exclude_unset.py" hl_lines="17 24 28"
--8<-- "pydantic-model-dump/exclude_unset.py"
```

Saída:

```text
{'bio'}
{'bio': None} {}
{'name': 'Ana'}
{'name': 'Ana', 'tags': ['admin', 'staff']}
```

Duas armadilhas:

!!! danger "1. Com `to_dict()`, um PATCH não consegue limpar campo"
    O cliente manda `{"bio": null}` querendo **apagar** a bio. O campo está
    em `model_fields_set` — ele foi passado —, mas o `exclude_none` do
    `to_dict()` o remove. O update chega vazio e a bio antiga fica. Se
    `null` tem significado no seu PATCH, use
    `model_dump(exclude_unset=True)`, sem `exclude_none`.

!!! warning "2. Mutação in-place não marca o campo"
    `model_fields_set` só registra **atribuição**. `tags.append("admin")`
    muda o valor, mas `tags` continua fora do conjunto, e o
    `exclude_unset` descarta a mudança. Reatribua
    (`obj.tags = [*obj.tags, "staff"]`) — com o `validate_assignment=True`
    do `BaseSchema`, a atribuição ainda passa pela validação.

## `exclude_defaults` e `exclude_none`

```python title="examples/pydantic-model-dump/exclude_defaults_none.py"
--8<-- "pydantic-model-dump/exclude_defaults_none.py"
```

Saída:

```text
{'name': 'Ana', 'bio': None, 'tags': []} {'name': 'Ana'}
{'name': 'Ana', 'tags': [], 'meta': {'avatar': None}}
```

- **`exclude_unset`** pergunta *"alguém passou?"*. **`exclude_defaults`**
  pergunta *"é igual ao default?"*. `bio=None` e `tags=[]` passados
  explicitamente sobrevivem ao primeiro e caem no segundo — inclusive com
  `default_factory`.
- **`exclude_none` só olha campos do model.** O `None` dentro de um
  `dict[str, Any]` (ou de uma lista) continua lá. Para limpar estrutura
  aninhada, a limpeza é sua.

## `exclude_computed_fields` e `round_trip`: o dump que volta a ser entrada

```python title="examples/pydantic-model-dump/computed_round_trip.py"
--8<-- "pydantic-model-dump/computed_round_trip.py"
```

Saída:

```text
{'width': 2, 'height': 3, 'area': 6} {'width': 2, 'height': 3}
recusou o próprio dump: extra_forbidden
{'payload': {'attempt': 1}} {'payload': '{"attempt":1}'}
sem round_trip: json_type
```

- **`@computed_field` sai no dump**, mas não é campo de entrada. Com
  `extra="forbid"`, o model **recusa o próprio dump**.
  `exclude_computed_fields=True` tira só esses.
- **`round_trip=True`** vai além: produz um dump que é entrada válida para o
  mesmo model. Tira os computed fields **e** devolve tipos não idempotentes
  na forma de entrada — um `Json[T]` volta a ser string JSON, em vez do
  `dict` já parseado que a validação recusaria.

!!! tip "Qual usar?"
    Quer reconstruir o model a partir do dump (cache, fila, snapshot)? Use
    `round_trip=True`. `exclude_computed_fields` é para quando só os computed
    fields atrapalham.

## `warnings` e `fallback`: quando um valor não serializa

```python title="examples/pydantic-model-dump/warnings_fallback.py" hl_lines="16 29 63"
--8<-- "pydantic-model-dump/warnings_fallback.py"
```

Saída:

```text
{'total': 'oops'}
warnings='error': PydanticSerializationUnexpectedValue(Expected `int` - serial
sem fallback: Unable to serialize unknown type: <class '__main__.Coordinate'>
{'location': {'lat': -5.09, 'lng': -42.8}}
```

**`warnings`** cuida de valor **fora do tipo declarado** — o que acontece
com `model_construct()` (que pula a validação) ou atribuição sem
`validate_assignment`:

| Valor | Efeito |
| --- | --- |
| `True` / `"warn"` (padrão) | serializa assim mesmo e emite `UserWarning` |
| `False` / `"none"` | serializa em silêncio |
| `"error"` | levanta `PydanticSerializationError` |

!!! tip "Em teste, use `\"error\"`"
    Por padrão o valor errado **sai** no dump, com um aviso que ninguém lê em
    produção. Em teste, `warnings="error"` transforma o aviso em falha.

**`fallback`** cuida de **tipo desconhecido**: um objeto que o Pydantic não
sabe serializar em `mode="json"`. Sem ele, `PydanticSerializationError`; com
ele, sua função recebe o objeto e devolve algo serializável (no exemplo,
`vars`).

## `serialize_as_any` e `polymorphic_serialization`: subclasses

Por padrão, o dump segue o **tipo declarado** do campo, não o tipo do
valor. Um `AdminSchema` num campo `UserSchema` sai só com os campos de
`UserSchema`. Os dois parâmetros mudam isso — de jeitos diferentes:

```python title="examples/pydantic-model-dump/polimorfismo.py" hl_lines="33 34 41 42"
--8<-- "pydantic-model-dump/polimorfismo.py"
```

Saída:

```text
{'lead': {'name': 'Ana'}}
{'lead': {'name': 'Ana', 'level': 9}}
{'lead': {'name': 'Ana', 'level': 9}}
{'lead': {'name': 'Bia'}}
{'lead': {'name': 'Bia', 'password_hash': '$2b$...'}}
```

- **`polymorphic_serialization=True`** serializa pelo tipo real **só quando
  ele é subclasse** do declarado (model ou dataclass Pydantic). Também pode
  ir no `model_config` da classe base.
- **`serialize_as_any=True`** é **duck typing**: serializa o valor pelo que
  ele é, seja qual for — inclusive um model sem relação nenhuma com o tipo
  declarado, ou chaves extras de um `TypedDict`.

!!! danger "O tipo declarado é um filtro de segurança"
    Declarar `lead: UserSchema` é também dizer *"só estes campos saem"*.
    `serialize_as_any=True` desliga esse filtro: o `LeakySchema` do exemplo
    vaza `password_hash`. Se você quer polimorfismo, prefira
    `polymorphic_serialization`, que só abre para subclasses que você
    escreveu.

## Recap

- **`mode="json"`** para tipos JSON; qualquer outra string, até `"JSON"`,
  vira `"python"` sem erro.
- **`include` / `exclude`**: `dict` desce na estrutura, `__all__` pega toda
  a lista, `exclude` ganha de `include`, `Field(exclude=True)` ganha de
  tudo.
- **`context`** só chega a serializers customizados.
- **`by_alias=None`** segue o `serialize_by_alias` da config.
- **`exclude_unset`** é o do PATCH — mas não vê mutação in-place, e o
  `to_dict()` do `BaseSchema` (com `exclude_none`) impede limpar campo com
  `null`.
- **`exclude_defaults`** compara com o default; **`exclude_none`** ignora
  `None` aninhado.
- **`round_trip=True`** gera dump que volta a ser entrada.
- **`warnings="error"`** em teste; **`fallback`** para tipo desconhecido.
- **`polymorphic_serialization`** para subclasses; **`serialize_as_any`**
  desliga o filtro do tipo declarado — cuidado com o que vaza. 🚨
