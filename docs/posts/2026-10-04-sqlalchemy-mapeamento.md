---
date:
  created: 2026-10-04 14:00:00
authors:
  - mauricio
categories:
  - tempest-fastapi-sdk
  - Python
tags:
  - sqlalchemy
  - banco de dados
  - alembic
slug: sqlalchemy-mapeamento
---

# SQLAlchemy 2: `Mapped`, `mapped_column`, `__table_args__` e constraints

O mapeamento declarativo do SQLAlchemy 2 parece só uma anotação de tipo por
coluna. Por baixo, cada detalhe vira DDL, e alguns deles quebram de um jeito
silencioso: uma anotação sem `mapped_column` que não cria coluna nenhuma, um
`onupdate` que em async vira `MissingGreenlet`, um índice que indexa uma
string literal e um SQLite que, por padrão, não confere chave estrangeira.

<!-- more -->

Como na [série sobre Pydantic](2026-10-04-pydantic-alias.md), todo exemplo é
um script que roda na CI do blog. Os que falam com banco usam **async**
(`aiosqlite`), como nos nossos serviços. ✅

!!! info "Versões"
    Medido com **SQLAlchemy 2.1.3**, **tempest-fastapi-sdk 0.303.0** e
    SQLite 3. O DDL de PostgreSQL vem do compilador do SQLAlchemy, sem banco
    rodando.

## Mapa rápido

| Pergunta | Onde mora |
| --- | --- |
| Tipo e `NULL` da coluna | `Mapped[T]` |
| Ajuste fino da coluna | `mapped_column(...)` |
| Tipo SQL padrão por tipo Python | `type_annotation_map`, `Annotated` |
| Default | `default`, `insert_default`, `server_default` |
| Valor ao atualizar | `onupdate`, `server_onupdate` |
| Constraint e índice de várias colunas, opções da tabela | `__table_args__` |
| Nome das constraints | `MetaData(naming_convention=...)` |

## `Mapped[T]`: tipo e nulidade

```python title="examples/sqlalchemy-mapeamento/mapped.py"
--8<-- "sqlalchemy-mapeamento/mapped.py"
```

Saída:

```text
CREATE TABLE product (
	id SERIAL NOT NULL,
	name VARCHAR NOT NULL,
	description VARCHAR,
	sku VARCHAR NOT NULL,
	price NUMERIC NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
	public_id UUID NOT NULL,
	PRIMARY KEY (id)
)

colunas: ['id', 'name', 'description', 'sku', 'price', 'created_at', 'public_id']
ProductModel.stock: 0
Mapped[dict]: MappedAnnotationError
```

O `Mapped[T]` é a fonte do tipo **e** da nulidade:

| Anotação | Resultado |
| --- | --- |
| `Mapped[str]` | `VARCHAR NOT NULL` |
| `Mapped[str \| None]` | `VARCHAR` (aceita `NULL`) |
| `Mapped[str \| None]` + `mapped_column(nullable=False)` | `NOT NULL` — o `nullable` explícito ganha |
| `Mapped[int]` + `primary_key=True` | `SERIAL` no PostgreSQL |
| `Mapped[datetime]` | `TIMESTAMP WITHOUT TIME ZONE` |

!!! danger "`Mapped[int] = 0` não cria coluna"
    Atribuir um valor cru a um atributo `Mapped` não define default: o
    SQLAlchemy trata aquilo como **atributo de classe comum**. A coluna
    `stock` não existe na tabela, e nada avisa. Default é sempre
    `mapped_column(default=0)`.

- **`Mapped[dict]`** (ou `list[str]`) não tem tipo SQL padrão:
  `MappedAnnotationError` na definição. Diga o tipo:
  `mapped_column(JSON)`.
- **`Mapped[datetime]`** vira timestamp **sem fuso**. O `BaseModel` do
  `tempest-fastapi-sdk` usa `UtcDateTime`, que é `TIMESTAMP WITH TIME ZONE`
  no PostgreSQL.

## Tipos reaproveitáveis: `type_annotation_map` e `Annotated`

```python title="examples/sqlalchemy-mapeamento/tipos_reusaveis.py"
--8<-- "sqlalchemy-mapeamento/tipos_reusaveis.py"
```

Saída:

```text
CREATE TABLE customer (
	id SERIAL NOT NULL,
	name VARCHAR(255) NOT NULL,
	document VARCHAR(50) NOT NULL,
	nickname VARCHAR(50),
	uf VARCHAR(2) NOT NULL,
	PRIMARY KEY (id)
)
```

- **`type_annotation_map`** na base declarativa troca o tipo SQL padrão de
  um tipo Python **para todo model**: aqui, todo `Mapped[str]` vira
  `VARCHAR(255)`.
- **`Annotated[str, mapped_column(String(50))]`** empacota tipo e
  configuração num nome (`Str50`, `IntPk`). E continua combinando com
  `| None`.
- Um tipo passado direto no `mapped_column(String(2))` ganha dos dois.

!!! tip "No `tempest-fastapi-sdk`"
    O `BaseModel` usa `type_annotation_map` para mandar todo
    `Mapped[SeuEnum]` para o `TempestEnum` — veja [Enum](#enum-nome-ou-valor)
    no fim do post.

## `mapped_column`: os parâmetros que mais aparecem

| Parâmetro | O que faz |
| --- | --- |
| 1º posicional `str` | nome da **coluna** no banco, quando difere do atributo |
| posicional tipo (`String(80)`, `JSON`) | tipo SQL, ganha do `Mapped` |
| posicional `ForeignKey(...)`, `Identity(...)`, `Computed(...)` | FK, identity, coluna gerada |
| `primary_key`, `nullable`, `unique`, `index` | o óbvio — veja as armadilhas abaixo |
| `default`, `insert_default`, `server_default` | default no Python ou no banco ([próxima seção](#default-no-python-ou-no-banco)) |
| `onupdate`, `server_onupdate` | valor ao atualizar ([seção do async](#onupdate-e-async-missinggreenlet)) |
| `comment` | comentário no banco (`COMMENT ON` no PostgreSQL) |
| `doc` | docstring do atributo Python, não vai ao banco |
| `deferred=True` | não carrega no `SELECT` até alguém ler — em async, ler depois é I/O |
| `sort_order` | ordem da coluna no `CREATE TABLE`, útil em mixin |

## Default: no Python ou no banco

```python title="examples/sqlalchemy-mapeamento/defaults.py"
--8<-- "sqlalchemy-mapeamento/defaults.py"
```

Saída:

```text
CREATE TABLE task (
	id SERIAL NOT NULL,
	priority INTEGER NOT NULL,
	status VARCHAR DEFAULT 'open' NOT NULL,
	attempts INTEGER DEFAULT 0 NOT NULL,
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL,
	PRIMARY KEY (id)
)

server_default=0: ArgumentError — use "0" ou text("0")
pelo ORM: 1 open 0
SQL cru: NOT NULL constraint failed: task.priority
```

| | `default` / `insert_default` | `server_default` |
| --- | --- | --- |
| Mora | no Python | no DDL (`DEFAULT ...`) |
| Vale para | INSERT feito pelo SQLAlchemy | qualquer INSERT, inclusive SQL cru, outra linguagem, migration |
| Aceita | valor, callable, expressão SQL | `str`, `text(...)`, expressão (`func.now()`) |

!!! danger "`default=` não existe para o banco"
    `priority` tem `default=1`, mas o `CREATE TABLE` diz só `NOT NULL`. Um
    INSERT por SQL cru — script de carga, outro serviço, migration de
    dados — falha com `NOT NULL constraint failed`. Se o valor precisa valer
    fora do ORM, ele precisa de `server_default`.

E `server_default=0` (um `int`) nem cria a classe: é `ArgumentError`. Use
`"0"` ou `text("0")`. A string é citada como literal (`DEFAULT 'open'`);
`text()` vai cru.

Repare também que, logo depois do `flush`, `task.status` e `task.attempts`
já têm valor sem `refresh`. No SQLAlchemy 2, quando o banco suporta
`RETURNING`, o INSERT já devolve os `server_default`.

## `onupdate` e async: `MissingGreenlet`

```python title="examples/sqlalchemy-mapeamento/onupdate_async.py"
--8<-- "sqlalchemy-mapeamento/onupdate_async.py"
```

Saída:

```text
py_updated_at: True
sql_updated_at: MissingGreenlet
awaitable_attrs: True
eager_defaults=True: True
```

O UPDATE do ORM roda o `onupdate`. Se ele é uma **função Python**
(`utcnow`), o valor é calculado antes e fica na instância. Se é uma
**expressão SQL** (`func.now()`), quem calcula é o banco, e o SQLAlchemy
marca o atributo como **expirado**: a próxima leitura vai ao banco buscar.

Em sessão síncrona isso é só uma query a mais. Em **async**, uma leitura de
atributo não pode fazer I/O, e o resultado é `MissingGreenlet`.

Três saídas:

1. **`onupdate` com callable Python** — o valor nunca expira.
2. **`__mapper_args__ = {"eager_defaults": True}`** — o UPDATE busca o valor
   novo com `RETURNING`.
3. **`await obj.awaitable_attrs.coluna`** (precisa do mixin `AsyncAttrs`) ou
   `await session.refresh(obj, ["coluna"])` — busca explícita.

!!! tip "É exatamente o que o `BaseModel` do SDK faz"
    O `updated_at` do `BaseModel` do `tempest-fastapi-sdk` usa
    `onupdate=utcnow` (callable, saída 1) **e** `server_default=func.now()`
    (para INSERT fora do ORM). O `created_at` combina `default=utcnow` com o
    mesmo `server_default`. A base também herda de `AsyncAttrs`.

## `__table_args__`

Tudo que não cabe numa coluna só — constraint composta, índice funcional,
schema, comentário da tabela — vai em `__table_args__`:

```python title="examples/sqlalchemy-mapeamento/table_args.py"
--8<-- "sqlalchemy-mapeamento/table_args.py"
```

Saída:

```text
billing.invoice | Notas fiscais emitidas
no_trailing_comma  ArgumentError
dict_first         ArgumentError
attribute_name     ConstraintColumnNotFoundError
```

As formas válidas:

- **`dict`** sozinho — só opções da tabela (`schema`, `comment`, opções de
  dialeto).
- **Tupla** de constraints e índices.
- **Tupla com o `dict` no fim** — as duas coisas.

E as três que quebram:

1. **`(UniqueConstraint("code"))` sem vírgula** não é tupla: parênteses
   sozinhos só agrupam. Escreva `(UniqueConstraint("code"),)`.
2. **`dict` fora do fim** da tupla.
3. **Nome do atributo Python** numa constraint: ela cita a **coluna do
   banco**. Com `email: Mapped[str] = mapped_column("email_address")`, a
   constraint precisa de `"email_address"`.

## Constraints e a convenção de nomes

```python title="examples/sqlalchemy-mapeamento/constraints.py"
--8<-- "sqlalchemy-mapeamento/constraints.py"
```

Saída:

```text
CREATE TABLE users (
	...
	PRIMARY KEY (id),
	UNIQUE (org_id, email),
	CONSTRAINT age_non_negative CHECK (age >= 0),
	FOREIGN KEY(org_id) REFERENCES org (id) ON DELETE CASCADE,
	UNIQUE (document)
)
CREATE INDEX ix_users_email_lower ON users (lower(email))
CREATE INDEX ix_users_org_id ON users (org_id)

CREATE TABLE c_users (
	...
	CONSTRAINT pk_c_users PRIMARY KEY (id),
	CONSTRAINT uq_c_users_org_id_email UNIQUE (org_id, email),
	CONSTRAINT ck_c_users_age_non_negative CHECK (age >= 0),
	CONSTRAINT fk_c_users_org_id_c_org FOREIGN KEY(org_id) REFERENCES c_org (id) ON DELETE CASCADE,
	CONSTRAINT uq_c_users_document UNIQUE (document)
)
CREATE INDEX ix_c_users_email_lower ON c_users (lower(email))
CREATE INDEX ix_c_users_org_id ON c_users (org_id)

CheckConstraint sem nome: Naming convention including %(constraint_name)s token requires that constraint is explicitly named.

índices da tag: ['ix_', 'ix_tag_title_lower']
CREATE INDEX ix_tag_title_lower ON tag (lower('title'))
```

**Sem convenção**, `UNIQUE`, `PRIMARY KEY` e `FOREIGN KEY` saem **sem
nome**, e o banco inventa um (`users_email_key`, `users_org_id_fkey`…), que
muda de um banco para outro. Na hora de uma migration apagar ou renomear a
constraint, o Alembic não sabe o nome dela.

**Com convenção**, todo nome é determinístico. O `BaseModel` do
`tempest-fastapi-sdk` já vem com `MetaData(naming_convention=NAMING_CONVENTION)`:

| Chave | Modelo | Exemplo |
| --- | --- | --- |
| `pk` | `pk_<tabela>` | `pk_c_users` |
| `uq` | `uq_<tabela>_<todas as colunas>` | `uq_c_users_org_id_email` |
| `ck` | `ck_<tabela>_<nome que você deu>` | `ck_c_users_age_non_negative` |
| `fk` | `fk_<tabela>_<colunas>_<tabela referida>` | `fk_c_users_org_id_c_org` |
| `ix` | `ix_<tabela>_<colunas>` | `ix_c_users_org_id` |

Três armadilhas na saída:

!!! danger "`CheckConstraint` precisa de `name=`"
    O modelo `ck` usa `%(constraint_name)s`, então um `CheckConstraint` sem
    nome **nem cria a classe**. Dê um nome curto que diga a regra
    (`age_non_negative`); a convenção põe o prefixo.

!!! danger "Índice funcional sem nome vira `ix_`"
    O modelo `ix` usa o nome da coluna, e uma expressão (`lower(slug)`) não
    tem nome de coluna. O índice sai como `ix_` — e o segundo índice
    funcional sem nome, em qualquer tabela, colide com ele. Índice funcional
    sempre com nome explícito.

!!! danger "`func.lower(\"title\")` indexa a string, não a coluna"
    Uma `str` dentro de `func.*` é um **valor**, não um nome de coluna: o DDL
    sai `lower('title')`, um índice sobre uma constante que não serve para
    nada. Use `func.lower(text("title"))` ou a coluna de verdade.

!!! note "`ON DELETE CASCADE` é do banco"
    `ForeignKey(..., ondelete="CASCADE")` vai para o DDL: quem apaga as
    linhas filhas é o banco. Isso é diferente de `cascade="all, delete"` num
    `relationship()`, que é o ORM apagando objeto por objeto.

## Índices, chaves compostas e `NULL` em `UNIQUE`

```python title="examples/sqlalchemy-mapeamento/indices.py"
--8<-- "sqlalchemy-mapeamento/indices.py"
```

Saída (PostgreSQL, depois SQLite, depois o envio):

```text
CREATE TABLE order_line (
	...
	CONSTRAINT pk_order_line PRIMARY KEY (order_id, position),
	CONSTRAINT uq_order_line_coupon UNIQUE NULLS NOT DISTINCT (coupon)
)
CREATE UNIQUE INDEX ix_order_line_sku ON order_line (sku)
CREATE UNIQUE INDEX ix_order_line_sku_active ON order_line (sku) WHERE deleted_at IS NULL

CREATE TABLE order_line (
	...
	CONSTRAINT pk_order_line PRIMARY KEY (order_id, position),
	CONSTRAINT uq_order_line_coupon UNIQUE (coupon)
)
CREATE UNIQUE INDEX ix_order_line_sku ON order_line (sku)
CREATE UNIQUE INDEX ix_order_line_sku_active ON order_line (sku) WHERE deleted_at IS NULL

CREATE TABLE shipment (
	...
	CONSTRAINT fk_shipment_order_id_line_position_order_line FOREIGN KEY(order_id, line_position) REFERENCES order_line (order_id, position) ON DELETE RESTRICT
)
```

- **Chave composta**: `PrimaryKeyConstraint` e `ForeignKeyConstraint` em
  `__table_args__`. A FK composta lista as colunas locais e as remotas na
  mesma ordem.
- **`unique=True` + `index=True`** na mesma coluna não cria constraint e
  índice: cria **um** `UNIQUE INDEX`. Sem o `index=True`, seria uma
  `UNIQUE` constraint.
- **Índice parcial**: `postgresql_where=` / `sqlite_where=`. É o jeito de ter
  "SKU único entre os registros não apagados" com soft delete.

!!! warning "`NULL` não conflita em `UNIQUE`"
    Por padrão, dois `NULL` numa coluna `UNIQUE` **não** colidem — no
    PostgreSQL e no SQLite. `postgresql_nulls_not_distinct=True` (PG 15+)
    muda isso, mas repare no DDL do SQLite: a opção **some sem aviso**. Um
    teste em SQLite nunca vai pegar essa regra.

## SQLite em teste: a chave estrangeira está desligada

A gente testa com SQLite em memória. Então vale saber o que o SQLite confere
por padrão:

```python title="examples/sqlalchemy-mapeamento/sqlite_fk.py"
--8<-- "sqlalchemy-mapeamento/sqlite_fk.py"
```

Saída:

```text
pragma padrão  FK para org inexistente: aceito
pragma padrão  org e membro no mesmo flush, sem relationship(): aceito
pragma padrão  CHECK: CHECK constraint failed: age_non_negative
pragma padrão  dois NULL em coluna unique: aceito
pragma padrão  membros da org apagada: 2
pragma ligado  FK: FOREIGN KEY constraint failed
pragma ligado  org e membro no mesmo flush, sem relationship(): FOREIGN KEY constraint failed
pragma ligado  CHECK: CHECK constraint failed: age_non_negative
pragma ligado  dois NULL em coluna unique: aceito
pragma ligado  membros da org apagada: 0
```

!!! danger "Sem `PRAGMA foreign_keys=ON`, FK e `CASCADE` não existem"
    Por padrão o SQLite **não confere chave estrangeira**: aceita membro de
    organização inexistente, e apagar a organização deixa os membros
    órfãos, com o `ON DELETE CASCADE` ignorado. `CHECK` funciona; FK não. O
    `PRAGMA` vale por conexão, então liga no evento `connect` do engine,
    como no `enable_foreign_keys` acima.

A segunda linha mostra um bug que o SQLite estava escondendo. Sem
`relationship()`, o SQLAlchemy **não sabe** que a organização precisa ser
inserida antes do membro, e manda os INSERTs fora de ordem. Com a FK
desligada, passa; com a FK ligada — e no PostgreSQL, sempre — quebra. Duas
saídas: declarar o `relationship()`, ou dar `await session.flush()` depois
de adicionar o pai.

## Enum: nome ou valor?

```python title="examples/sqlalchemy-mapeamento/enums_sdk.py"
--8<-- "sqlalchemy-mapeamento/enums_sdk.py"
```

Saída:

```text
CREATE TABLE plain_account (
	id INTEGER NOT NULL,
	status VARCHAR(9) NOT NULL,
	PRIMARY KEY (id)
)

CREATE TABLE account (
	status VARCHAR(9) NOT NULL,
	...
	CONSTRAINT ck_account_status_enum CHECK (status IN ('active', 'suspended'))
)

CREATE TABLE account (
	status status_enum NOT NULL,
	...
)

padrão grava: ACTIVE | SDK grava: active
```

O `Mapped[Status]` padrão do SQLAlchemy grava o **nome** do membro
(`ACTIVE`) e, no SQLite, não cria `CHECK` nenhum. Renomear o membro no
Python passa a invalidar dado gravado, e um `UPDATE` cru aceita qualquer
texto.

O `BaseModel` do `tempest-fastapi-sdk` grava o **valor** (`active`), cria
`CHECK` nos bancos sem enum nativo e dá ao tipo do PostgreSQL um nome que
não colide (`status_enum`) — tudo pelo `type_annotation_map`, sem você
escrever nada além de `Mapped[Status]`.

## Recap

- **`Mapped[T]`** decide tipo e nulidade; `T | None` aceita `NULL`, e um
  `nullable=` explícito ganha.
- **`Mapped[int] = 0` não cria coluna** — default é `mapped_column(default=0)`.
- **`type_annotation_map` e `Annotated`** declaram o tipo uma vez só.
- **`default` mora no Python**; SQL cru só vê `server_default`. E
  `server_default` não aceita `int`.
- **`onupdate=func.now()` em async é `MissingGreenlet`** — use callable
  Python, `eager_defaults=True` ou `awaitable_attrs`.
- **`__table_args__`**: tupla com vírgula, `dict` no fim, nome de coluna do
  banco.
- **Convenção de nomes** (já vem no `BaseModel` do SDK): `CheckConstraint`
  precisa de `name=`, índice funcional precisa de nome, e `func.lower("x")`
  indexa uma string.
- **`NULL` não colide em `UNIQUE`**, e `NULLS NOT DISTINCT` some no SQLite.
- **SQLite não confere FK** sem `PRAGMA foreign_keys=ON` — e isso esconde
  INSERT fora de ordem quando falta `relationship()`.
- **Enum padrão grava o nome**; o `BaseModel` do SDK grava o valor. 🚀
