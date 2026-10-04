# Blog Tempest

Blog público do Projeto Tempest sobre as tecnologias que usamos e construímos:
Python + [`tempest-fastapi-sdk`](https://pypi.org/project/tempest-fastapi-sdk/)
no backend, JavaScript + [`tempest-react-sdk`](https://www.npmjs.com/package/tempest-react-sdk)
no frontend.

🌐 **<https://tempesttecnology.github.io/blog/>** · RSS:
[`feed_rss_created.xml`](https://tempesttecnology.github.io/blog/feed_rss_created.xml)

Feito com [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) e o
[plugin de blog](https://squidfunk.github.io/mkdocs-material/plugins/blog/)
dele, publicado no GitHub Pages a cada push na `main`.

## Rodar localmente

Requer [`uv`](https://docs.astral.sh/uv/).

```bash
uv run --group docs mkdocs serve
```

Abra <http://127.0.0.1:8000/blog/>. Rascunhos (`draft: true`) aparecem só no
`serve`, nunca no build publicado.

Antes do PR, confira o build como a CI roda:

```bash
uv run --group docs mkdocs build --strict
```

## Escrever um post

1. Crie `docs/posts/AAAA-MM-DD-<slug>.md`:

    ```markdown
    ---
    date:
      created: 2026-10-04
    authors:
      - mauricio
    categories:
      - FastAPI
    tags:
      - sqlalchemy
    slug: meu-post
    draft: true
    ---

    # Título do post

    Parágrafo de abertura — vira o resumo na página inicial.

    <!-- more -->

    Resto do post.
    ```

2. O marcador `<!-- more -->` é **obrigatório**: separa o resumo do corpo.
3. `categories` aceita só as listadas em `categories_allowed` no
   `mkdocs.yml`. As duas primeiras viram abas no topo do site:
   `tempest-fastapi-sdk` (backend) e `tempest-react-sdk` (frontend). As
   demais: Python, FastAPI, JavaScript, React, Visão Computacional,
   Arquitetura, Comunidade. Precisa de outra? Adicione lá no mesmo PR.
4. Autor novo entra em `docs/.authors.yml`.
5. Imagens vão ao lado do post ou em `docs/assets/`.
6. **Código do post é testado.** Exemplo Python vira script em
   `examples/<post>/`, com `assert` fixando o comportamento, e entra no post
   por snippet:

    ````markdown
    ```python title="examples/meu-post/exemplo.py"
    --8<-- "meu-post/exemplo.py"
    ```
    ````

    A CI roda todo `examples/*/*.py`; se a biblioteca mudar de
    comportamento, o build quebra antes do post mentir. Rode local com
    `uv run --group examples python examples/<post>/<arquivo>.py`.
7. Tire o `draft: true` e abra o PR. A CI valida o build com `--strict`; o
   merge na `main` publica.

## Estrutura

```text
.
├── mkdocs.yml               # tema, plugins, categorias permitidas
├── pyproject.toml           # grupo de dependência `docs`
├── docs/
│   ├── index.md             # página inicial (lista de posts)
│   ├── sobre.md
│   ├── .authors.yml
│   ├── assets/
│   ├── category/            # descrição das abas tempest-*-sdk
│   └── posts/               # um arquivo por post
├── examples/                # código dos posts, executado na CI
└── .github/workflows/deploy.yml
```

## Licença

Texto dos posts sob [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
