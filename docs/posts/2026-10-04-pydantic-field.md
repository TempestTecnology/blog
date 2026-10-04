---
date:
  created: 2026-10-04 12:00:00
authors:
  - mauricio
categories:
  - tempest-fastapi-sdk
  - Python
tags:
  - pydantic
  - fastapi
  - validação
slug: pydantic-field
---

# Todos os parâmetros do `Field()`

`Field()` aceita **36 parâmetros**. Uns mudam a validação, outros só o JSON
Schema, outros só a serialização — e alguns só funcionam em dataclass. Este
post passa por todos, com o que a docstring não conta: default que nunca é
validado, `pattern` que casa no meio da string, `float` que vira `null` no
JSON e constraint no tipo errado que vira **500** em vez de **422**.

<!-- more -->

Como nos posts sobre [`alias`](2026-10-04-pydantic-alias.md) e
[`model_dump()`](2026-10-04-pydantic-model-dump.md), todo exemplo é um script
com `assert` que roda na CI do blog. ✅

!!! info "Versões"
    Medido com **Pydantic 2.13.5**.

## Mapa rápido

| Grupo | Parâmetros |
| --- | --- |
| Default | `default`, `default_factory`, `validate_default` |
| Nome | `alias`, `alias_priority`, `validation_alias`, `serialization_alias` |
| JSON Schema | `title`, `field_title_generator`, `description`, `examples`, `json_schema_extra`, `deprecated` |
| Saída | `exclude`, `exclude_if`, `repr` |
| União | `discriminator`, `union_mode` |
| Mutabilidade | `frozen` |
| Só dataclass | `init`, `init_var`, `kw_only` |
| Texto | `pattern`, `min_length`, `max_length`, `strict`, `coerce_numbers_to_str` |
| Número | `gt`, `ge`, `lt`, `le`, `multiple_of`, `allow_inf_nan`, `max_digits`, `decimal_places` |
| Coleção | `min_length`, `max_length`, `fail_fast` |
| Legado | `**extra` |

Os quatro de nome já têm [um post só deles](2026-10-04-pydantic-alias.md) —
aqui ficam de fora.

## Default: `default`, `default_factory`, `validate_default`

```python title="examples/pydantic-field/default.py"
--8<-- "pydantic-field/default.py"
```

Saída:

```text
first_name='Ana' roles=['admin'] tags=[] slug='ana'
first_name='Bia' roles=[] tags=[] slug='bia'
retries='três' retries=3
default + default_factory: cannot specify both default and default_factory
factory antes do campo que ela lê: KeyError 'first_name'
```

- **Default mutável não é compartilhado.** Diferente de função Python,
  `roles: list[str] = []` é copiado por instância: o `append` na Ana não
  aparece na Bia. `default_factory=list` continua sendo a forma explícita.
- **`default_factory` pode receber os dados já validados** — basta a função
  ter um parâmetro. Mas só enxerga campos **declarados antes**: invertida a
  ordem, `KeyError`.
- **`default` e `default_factory` juntos** é `TypeError` na definição.

!!! danger "O default não é validado"
    `retries: int = "três"` cria a classe, cria a instância e entrega uma
    `str` num campo `int` — sem erro. O Pydantic confia no default por
    performance. `validate_default=True` faz ele passar pela validação (e
    pela conversão: `"3"` vira `3`).

## JSON Schema: `title`, `description`, `examples`, `json_schema_extra`, `deprecated`

Estes não mudam a validação. Mudam o JSON Schema — e, no FastAPI, o que
aparece no Swagger (`/docs`).

```python title="examples/pydantic-field/metadados.py"
--8<-- "pydantic-field/metadados.py"
```

Saída (resumida):

```text
"name":       {"title": "Nome", "description": "Nome exibido na vitrine.", "examples": ["Café"], ...}
"unit_price": {"title": "Unit Price", "x-unit": "centavos", ...}
"stock":      {"minimum": 0, ...}
"old_price":  {"deprecated": true, ...}
ao ler old_price: Use unit_price.
```

- **`title`** fixa o título; **`field_title_generator`** calcula a partir do
  nome do campo. Também existe no `model_config`, para o model inteiro.
- **`json_schema_extra`** aceita `dict` (mesclado) ou função (recebe o schema
  e muda no lugar).
- **`deprecated`** marca `"deprecated": true` no schema e emite
  `DeprecationWarning` **ao ler** o atributo. Receber o campo na entrada não
  avisa nada — quem usa a API não fica sabendo.

!!! tip "`minimum` no schema não é validação"
    O `"minimum": 0` que o `json_schema_extra` colocou é **só documentação**:
    `stock=-5` passa. Quer validar? Use `ge=0`, que valida **e** documenta.

## Saída: `exclude`, `exclude_if`, `repr`

```python title="examples/pydantic-field/serializacao.py"
--8<-- "pydantic-field/serializacao.py"
```

Saída:

```text
SessionSchema(password_hash='$2b$...', note=None)
{'token': 'abc'}
schema de entrada: ['password_hash', 'note', 'token']
schema de saída: ['note', 'token']
```

- **`exclude=True`** tira o campo do `model_dump()` e do schema de **saída**.
  Ele continua no schema de **entrada** — é um campo que se recebe e nunca
  se devolve.
- **`exclude_if`** decide por valor, a cada dump: aqui, a `note` só sai
  quando não é `None`.
- **`repr=False`** tira o campo do `repr()` — e só dele.

!!! danger "`exclude` não protege o `repr`"
    Repare na primeira linha da saída: `password_hash` sai no `repr`. Quem
    loga o objeto (`logger.info(f"{session}")`) vaza o hash. Campo sensível
    precisa de `exclude=True` **e** `repr=False` — um não implica o outro.

## União: `discriminator` e `union_mode`

```python title="examples/pydantic-field/discriminator.py"
--8<-- "pydantic-field/discriminator.py"
```

Saída:

```text
TaggedSchema [('missing', ('payment', 'card', 'last4'))]
PlainSchema [('literal_error', ('payment', 'PixSchema', 'method')), ('missing', ('payment', 'PixSchema', 'key')), ('missing', ('payment', 'CardSchema', 'last4'))]
payment=PixSchema(method='pix', key='a@b.com')
```

Sem discriminador, o Pydantic tenta **cada** membro da união e devolve o
erro de todos — três erros para um campo faltando. Com
`discriminator="method"`, ele lê a chave, vai direto ao `CardSchema` e
devolve **um** erro, o certo. Mais rápido, e a mensagem para o cliente faz
sentido.

`union_mode` vale para união sem discriminador:

```python title="examples/pydantic-field/union_fail_fast.py" hl_lines="9 10"
--8<-- "pydantic-field/union_fail_fast.py"
```

Saída:

```text
smart='1' left_to_right=1
[('fast', 0), ('full', 0), ('full', 1), ('full', 2)]
```

- **`"smart"`** (padrão) prefere o membro onde o valor **já é** do tipo:
  `"1"` é `str`, fica `str`.
- **`"left_to_right"`** aceita o **primeiro** que validar, convertendo: `int`
  vem antes e aceita `"1"`, vira `1`.

(A segunda linha é o `fail_fast`, mais abaixo.)

## `frozen`

```python title="examples/pydantic-field/frozen.py"
--8<-- "pydantic-field/frozen.py"
```

Saída:

```text
atribuição: frozen_field
model_copy: id=999 status='open'
hash: unhashable type: 'InvoiceSchema'
```

!!! warning "`frozen` é por atribuição, não por valor"
    `model_copy(update=...)` não valida nada e troca o campo congelado sem
    reclamar. E um campo `frozen` não torna o model hasheável — para isso é
    `model_config = ConfigDict(frozen=True)`, no model inteiro.

## Só dataclass: `init`, `init_var`, `kw_only`

```python title="examples/pydantic-field/dataclass.py"
--8<-- "pydantic-field/dataclass.py"
```

Saída:

```text
UserRecord(email='ana@x.com', password_hash='hash(s3cret)')
email posicional: ['missing']
Field(init_var=True): ['unexpected_positional_argument']
counter=5
```

- **`init=False`**: o campo não entra no construtor (precisa de default).
- **`kw_only=True`**: só por nome — posicional dá `missing`.
- **`init_var`**: o valor entra no construtor, vai para o `__post_init__` e
  **não fica guardado**.

!!! danger "Use `InitVar[...]`, não `Field(init_var=True)`"
    A anotação `InitVar[str]` liga o `init_var` por dentro e funciona.
    Escrever `Field(init_var=True)` à mão faz o Pydantic **pular o campo
    inteiro**: ele some do construtor e passar o valor dá
    `unexpected_positional_argument`.

!!! note "Em `BaseModel`, os três são ignorados"
    Sem erro e sem aviso: `Field(init=False)` num `BaseModel` continua
    aceitando o campo no construtor.

## Texto: `pattern`, tamanho, `strict`, `coerce_numbers_to_str`

```python title="examples/pydantic-field/strings.py"
--8<-- "pydantic-field/strings.py"
```

Saída:

```text
loose='abc123xyz' anchored='123'
ancorado: string_pattern_mismatch
lookahead no motor Rust: SchemaError na definição da classe
password='segredo1'
uf='PI' items=[1]
quantity=1 document='12345678900'
strict com '1': int_type
strict com 1.0: int_type
```

!!! danger "`pattern` procura, não casa a string inteira"
    `pattern=r"\d{3}"` aceita `"abc123xyz"`: basta **conter** três dígitos.
    Para validar a string toda, ancore: `^...$`.

- **Lookahead** (`(?=...)`) não existe no motor de regex padrão, que é em
  Rust: a classe nem é criada (`SchemaError`). `regex_engine="python-re"` no
  `model_config` troca para o `re` do Python.
- **`min_length` / `max_length`** valem para `str` e coleções, e contam
  **depois** do `str_strip_whitespace` — `"  PI  "` passa com
  `max_length=2`.
- **`strict=True`** recusa conversão: nem `"1"` nem `1.0` viram `int`.
- **`coerce_numbers_to_str=True`** faz o contrário num `str`: aceita número
  e converte. Útil para CPF/CEP que chegam como número.

## Número: limites, `allow_inf_nan`, `Decimal`

```python title="examples/pydantic-field/numeros.py"
--8<-- "pydantic-field/numeros.py"
```

Saída:

```text
score=9.5 temperature=inf safe_temperature=0 price=Decimal('0')
{"score":9.5,"temperature":null,"safe_temperature":0.0,"price":"0"}
score=11               less_than_equal
score=7.3              multiple_of
score=nan              less_than_equal
safe_temperature=inf   finite_number
price=1234.5           decimal_whole_digits
price=1.234            decimal_max_places
score=1.0 temperature=0 safe_temperature=0 price=Decimal('1.2300')
TypeError, não ValidationError: Unable to apply constraint 'max_digits' to supplied value 12345
```

- **`gt` / `ge` / `lt` / `le` / `multiple_of`**: limites. `NaN` falha em
  qualquer comparação, então um campo com limite já recusa `nan`.
- **`max_digits`** conta dígitos no total; **`decimal_places`**, depois da
  vírgula. Os dois são para **`Decimal`** — a docstring do Pydantic diz "for
  strings", mas não é. Zeros à direita não contam: `"1.2300"` passa com
  `decimal_places=2`.

!!! danger "`float` aceita `inf` e vira `null` no JSON"
    Por padrão `float` aceita `"inf"`, `"-inf"` e `"nan"`. No
    `model_dump_json()`, `inf` sai como **`null`** — o dado some sem erro.
    Em campo sem limite, use `allow_inf_nan=False`.

!!! danger "Constraint no tipo errado: 500 em vez de 422"
    `Field(max_digits=3)` num `str` (ou `gt=3` num `str`) **cria a classe
    sem erro**. A falha só aparece na validação, e como `TypeError`, não
    `ValidationError`. No FastAPI, isso é **500** para o cliente, não 422.
    Um teste que instancia o schema uma vez pega isso antes do deploy.

## Coleção: `fail_fast`

Na saída do `union_fail_fast.py` acima: `fast` parou no **primeiro** item
inválido; `full` reportou os três. `fail_fast=True` economiza trabalho em
lista grande quando um erro basta. Vale para `list`, `tuple`, `set` e
`frozenset` — em `dict`, a classe nem é criada.

## Legado: `**extra`

`Field(default=0, foo="bar")` ainda funciona: `foo` vai para o JSON Schema,
com `PydanticDeprecatedSince20`. Vai sair na v3 — use
`json_schema_extra={"foo": "bar"}`.

## Recap

- **Default não é validado**; `validate_default=True` valida.
  `default_factory` com parâmetro lê só campos declarados antes.
- **Metadados** mudam o schema e o Swagger, não a validação. `deprecated`
  avisa só quem **lê** o atributo.
- **`exclude=True` não esconde do `repr`** — campo sensível precisa de
  `repr=False` também.
- **`discriminator`** dá um erro certo em vez de N errados.
- **`frozen`** bloqueia atribuição, não `model_copy(update=...)`.
- **Dataclass**: use `InitVar[...]`, nunca `Field(init_var=True)`. Em
  `BaseModel`, `init`/`init_var`/`kw_only` são ignorados.
- **`pattern` procura** — ancore com `^...$`. Lookahead pede
  `regex_engine="python-re"`.
- **`float` aceita `inf`** e vira `null` no JSON: `allow_inf_nan=False`.
- **`max_digits` / `decimal_places`** são de `Decimal`. Constraint no tipo
  errado é `TypeError` em runtime — 500, não 422. 🚨
