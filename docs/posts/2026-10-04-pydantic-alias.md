---
date:
  created: 2026-10-04 10:00:00
authors:
  - mauricio
categories:
  - tempest-fastapi-sdk
  - Python
tags:
  - pydantic
  - fastapi
  - schemas
slug: pydantic-alias
---

# Os três `alias` do Pydantic: direção, prioridade e o nome do campo

`alias`, `validation_alias` e `serialization_alias` parecem três jeitos de
dizer a mesma coisa. Não são: cada um age numa **direção**, o
`alias_priority` não faz o que o nome sugere, e com o `BaseSchema` do
`tempest-fastapi-sdk` um alias mal entendido pode **descartar um valor sem
erro nenhum**.

<!-- more -->

Todo exemplo deste post é um script completo, com `assert`, que roda na CI do
blog a cada push. Se o Pydantic mudar de comportamento, o build quebra antes
do post mentir. ✅

!!! info "Versões"
    Medido com **Pydantic 2.13.5** e **tempest-fastapi-sdk 0.303.0**.
    `validate_by_name` existe a partir do Pydantic **2.11**.

## Cada alias tem uma direção

Pense no schema como uma porta com dois sentidos:

- **Entrada** — `dict` → model (`model_validate`, o body do request no
  FastAPI).
- **Saída** — model → `dict` (`model_dump(by_alias=True)`, o response).

| Parâmetro | Entrada aceita | Saída (`by_alias=True`) |
| --- | --- | --- |
| `alias="X"` | `X` | `X` |
| `validation_alias="X"` | `X` | nome do campo |
| `serialization_alias="X"` | nome do campo | `X` |

```python title="examples/pydantic-alias/direcao.py"
--8<-- "pydantic-alias/direcao.py"
```

Saída:

```text
AliasSchema recusou user_id: missing
ValidationAliasSchema recusou user_id: missing
{'user_id': 1}
```

Repare em duas coisas:

1. Com `alias` ou `validation_alias`, mandar `user_id` (o nome do campo) na
   entrada **falha** com `missing`. O alias não é um apelido extra — ele
   **substitui** o nome do campo na entrada. Já já voltamos nisso.
2. `model_dump()` sem `by_alias=True` usa o nome do campo, mesmo com
   `alias`. A saída só usa o alias quando você pede.

!!! tip "No FastAPI"
    O `response_model` serializa com `by_alias=True` por padrão. Por isso um
    `alias` aparece no JSON de resposta mesmo sem você pedir nada.

## `alias` é só a abreviação

`alias` preenche os outros dois. Se você passa `validation_alias` junto, ele
toma a entrada, e o `alias` sobra só para a saída:

```python title="examples/pydantic-alias/combinados.py" hl_lines="9 15 16"
--8<-- "pydantic-alias/combinados.py"
```

Saída:

```text
{'orderId': 7}
customer_id=9 city='Teresina'
```

`validation_alias` aceita dois tipos que os outros não aceitam:

- **`AliasChoices("customer_id", "ID")`** — vários nomes aceitos, testados
  **em ordem**. No exemplo o payload traz os dois e ganha `customer_id`, o
  primeiro da lista.
- **`AliasPath("addresses", 1, "city")`** — caminho aninhado: chave, índice
  de lista, chave.

!!! warning "Só em `validation_alias`"
    `alias` e `serialization_alias` são tipados como `str`. Passar um
    `AliasChoices` em `alias` até roda, mas o type-checker recusa e a
    intenção fica escondida. Nome múltiplo ou caminho é coisa de entrada:
    use `validation_alias`.

## `alias_priority` não é disputa entre eles

O nome engana: `alias_priority` **não** decide qual dos três alias ganha em
runtime. Ele decide se o `alias_generator` do `model_config` pode
**sobrescrever** o que você escreveu no `Field`.

| Como o campo foi declarado | `alias_priority` | O gerador… |
| --- | --- | --- |
| Algum dos três alias, sem `alias_priority` | `2` (padrão) | não mexe no que você escreveu |
| Algum alias **e** `alias_priority=1` | `1` | sobrescreve o que você escreveu |
| Nenhum alias | `1` | preenche |

```python title="examples/pydantic-alias/prioridade.py" hl_lines="12 13"
--8<-- "pydantic-alias/prioridade.py"
```

Saída:

```text
unit_price   alias='PRICE'        alias_priority=2
stock_count  alias='stockCount'   alias_priority=1
created_by   alias='createdBy'    alias_priority=1
```

`stock_count` declarou `alias="STOCK"`, mas com `alias_priority=1` o
`to_camel` passou por cima: o alias final é `stockCount`, e `"STOCK"` deixa de
existir. `unit_price`, com a prioridade padrão, manteve `"PRICE"`.

## A trava é por slot, não por campo

Aqui mora a pegadinha que só aparece no código-fonte. A prioridade `2`
protege **o que você escreveu** — não o campo inteiro. Os slots que você
deixou vazios o gerador continua preenchendo:

```python title="examples/pydantic-alias/por_slot.py" hl_lines="12"
--8<-- "pydantic-alias/por_slot.py"
```

Saída:

```text
alias='dueDate'
validation_alias='VENCIMENTO'
serialization_alias='dueDate'
alias_priority=2
```

Você declarou só `validation_alias`, e mesmo assim o campo ganhou
`alias` **e** `serialization_alias` vindos do gerador. A resposta da API sai
com `dueDate` — um nome que não aparece em lugar nenhum da declaração do
campo.

## O nome do campo deixa de valer

Voltando ao primeiro exemplo: com `alias`, o nome do campo é **inválido** na
entrada. Para aceitar os dois, ligue no `model_config`:

```python
model_config = ConfigDict(validate_by_name=True, validate_by_alias=True)
```

!!! note "E o `populate_by_name`?"
    É o nome antigo da mesma ideia. Desde o Pydantic 2.11 o uso não é
    recomendado e ele vai ser deprecado na v3 — prefira `validate_by_name`.
    E não existe `validate_by_name` no `Field`: é configuração do model.

### Por que isso importa no `tempest-fastapi-sdk`

O `BaseSchema` do SDK traz `extra="ignore"`: chave desconhecida no payload é
descartada em silêncio. Junte isso a um alias e o nome do campo vira uma
**chave desconhecida**:

```python title="examples/pydantic-alias/nome_do_campo.py" hl_lines="10 21 23"
--8<-- "pydantic-alias/nome_do_campo.py"
```

Saída:

```text
sem validate_by_name: page_size=20
com validate_by_name: page_size=100 | page_size=50
```

!!! danger "Valor descartado sem erro"
    Em campo **obrigatório**, mandar o nome do campo falha alto com
    `missing` — você descobre no primeiro teste. Em campo **opcional**, o
    `extra="ignore"` engole a chave e o default entra no lugar: o cliente
    pediu `page_size=100`, recebeu 20, e nenhum log registra nada.

Se um schema seu tem alias em campo opcional e o cliente pode mandar
qualquer um dos dois nomes, `validate_by_name=True` não é preferência — é o
que separa "funciona" de "funciona às vezes".

## Recap

- **Direção**: `alias` = entrada + saída; `validation_alias` = só entrada;
  `serialization_alias` = só saída.
- **`alias` é abreviação**: com `validation_alias` junto, ele sobra só para a
  saída.
- **`AliasChoices` e `AliasPath`** só em `validation_alias`; `AliasChoices`
  testa em ordem.
- **`alias_priority`** decide se o `alias_generator` sobrescreve o `Field`:
  `2` (padrão com alias) protege, `1` libera.
- **A trava é por slot**: o gerador preenche os alias que você deixou vazios.
- **Com alias, o nome do campo é inválido na entrada** — ligue
  `validate_by_name=True` no `model_config`. No `BaseSchema`, com
  `extra="ignore"`, esquecer isso descarta valor de campo opcional em
  silêncio. 🚨
