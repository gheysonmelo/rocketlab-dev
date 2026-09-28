# CineFILO — Sistema de Avaliação de Filmes

Módulo administrativo de um catálogo de filmes inspirado no Letterboxd, desenvolvido na
atividade DEV do **Rocket Lab 2026 (Visagio)**. O administrador navega por um catálogo de
~95 mil filmes, vê a ficha completa e o histórico de avaliações, cadastra, edita e remove
filmes, e registra notas (em meia estrela) e resenhas.

> **Sobre o nome:** *CineFILO* vem de inspiração no **FILO**, um projeto pessoal meu. A
> identidade visual (tipografia Outfit, paleta, painéis e cards) segue o protótipo de alta
> fidelidade do FILO no Figma.

| Camada | Tecnologias |
| --- | --- |
| Frontend | Vite, React 19, TypeScript, Tailwind CSS 4, React Router, TanStack Query |
| Backend | FastAPI, SQLAlchemy 2 (assíncrono), Alembic, Pydantic 2 |
| Banco | SQLite |
| Qualidade | pytest (82 testes), Ruff, oxlint |
| Autenticação | JWT (PyJWT), com o token enviado como `Bearer` |

## Requisitos atendidos

| Requisito | Onde |
| --- | --- |
| Cadastrar filmes (título, diretor, ano, gênero, sinopse…) | **Novo filme** · `POST /api/v1/movies` |
| Catálogo paginado | Tela inicial · `GET /api/v1/movies?page=&page_size=` |
| Detalhes + avaliações já feitas | Clique no card · `GET /api/v1/movies/{id}` e `/reviews` |
| Barra de pesquisa | Campo **Buscar** · `GET /api/v1/movies?q=` |
| Remover e atualizar filmes | **Editar** / **Excluir** na ficha · `PUT` / `DELETE /api/v1/movies/{id}` |
| Nova avaliação (1 a 5 estrelas + resenha) | Formulário na ficha, em meia estrela · `POST /api/v1/movies/{id}/reviews` |
| Média geral de cada filme | Cards e ficha, com a fração exata da estrela (4,4 = quatro cheias e uma 40% cheia) |

**Extras:** login do administrador com JWT, filtros por gênero, status e ano (combináveis com a busca e guardados na URL), paginação numerada com escolha de itens por página, layout responsivo (no celular, a navegação vira uma barra fixa embaixo) e cache de consultas com TanStack Query.

## Como executar

### Pré-requisitos

- **Python 3.11+** e **Node.js 20.19+**

### 1. CSVs

Os CSVs da atividade **já vêm no repositório**, nas pastas `bases_atv_dev1/` e
`bases_atv_dev_2/` (~230 MB), então basta clonar. A carga procura os arquivos pelo nome,
inclusive em subpastas; para usar CSVs de outro local, passe `--data-dir`.

### 2. Backend (http://localhost:8000)

No Windows (Git Bash ou PowerShell), dentro de `backend/`:

```bash
python -m venv .venv
source .venv/Scripts/activate      # PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head               # cria as tabelas
python -m app.scripts.seed         # carrega e limpa os CSVs (~1 min 30 s)
uvicorn app.main:app --reload
```

No Linux/macOS o fluxo é o mesmo, com `python3` e `source .venv/bin/activate`.

- Documentação interativa: http://localhost:8000/docs
- **Login:** usuário `admin`, senha `cinefilo` (definidos em `ADMIN_USERNAME` e `ADMIN_PASSWORD` no `.env`; troque também o `JWT_SECRET` fora do ambiente local)
- Recarregar os dados do zero: `python -m app.scripts.seed --reset`
- Menos log de SQL no terminal: `ENVIRONMENT=dev` no `.env`

### 3. Frontend (http://localhost:5173)

Em outro terminal, dentro de `frontend/`:

```bash
npm install
npm run dev
```

O Vite repassa `/api` para o backend em `127.0.0.1:8000`, então não é preciso configurar CORS.

### Testes e lint

```bash
# backend/
python -m pytest
ruff check .

# frontend/
npm run lint
npm run build      # inclui a checagem de tipos
```

## Estrutura

```text
backend/app/
├── core/          # configurações, paginação, erros de domínio
├── movies/
│   ├── models.py      # modelo estrela (repositório base)
│   ├── schemas.py     # contratos Pydantic de entrada e saída
│   ├── repository.py  # consultas (catálogo, ficha, avaliações, gêneros)
│   ├── service.py     # regras de escrita (filmes e avaliações)
│   └── router.py      # endpoints
└── scripts/
    ├── seed.py        # carga dos CSVs
    └── cleaning.py    # regras de limpeza dos dados

frontend/src/
├── api/           # tipos do contrato, cliente fetch e hooks do TanStack Query
├── components/    # Layout, MovieCard, StarRating, StarRatingInput, Select, ReviewSection…
├── lib/           # estrelas, formatação pt-BR, paginação
└── pages/         # Catálogo, Ficha do filme, Formulário (novo/editar)
```

## API (`/api/v1`)

| Método | Rota | Descrição |
| --- | --- | --- |
| POST | `/auth/login` | Login do administrador; devolve o token JWT |
| GET | `/auth/me` | Usuário do token |
| GET | `/movies?page=&page_size=&q=&genero_id=&ano=&status=` | Catálogo paginado, com busca pelo título e filtros |
| GET | `/movies/{id}` | Ficha: equipe, elenco, produtoras, desempenho e média |
| POST | `/movies` | Cadastra um filme |
| PUT | `/movies/{id}` | Atualiza um filme |
| DELETE | `/movies/{id}` | Remove o filme e suas avaliações |
| GET | `/movies/{id}/reviews` | Avaliações paginadas, mais recentes primeiro |
| POST | `/movies/{id}/reviews` | Nova avaliação (`nome`, `nota` de 1 a 10, `comentario`) |
| DELETE | `/movies/{id}/reviews/{review_id}` | Remove uma avaliação |
| GET | `/genres` | Gêneros disponíveis |

## Decisões técnicas

**Autenticação.** Há um único administrador, com as credenciais no `.env`, então não foi
necessária uma tabela de usuários nem uma migração. `POST /auth/login` devolve um JWT
(HS256, 8 h). As rotas de leitura são públicas, e as de escrita (criar, editar e excluir filmes;
criar e excluir avaliações) exigem `Authorization: Bearer <token>`, respondendo 401 sem ele.
No front, todas as telas pedem login, e um token expirado leva de volta ao login.

**Escala das notas.** O banco guarda notas de 0 a 10 (restrição do modelo base e escala dos
CSVs). A interface usa estrelas de 0,5 a 5, como no Letterboxd: cada meia estrela vale 1
ponto (4,5 estrelas = 9). A média exibida é `média ÷ 2`, desenhada com a fração exata.

**Média coerente com as avaliações.** O `dim_reviews.csv` não bate com o
`movies_reviews.csv` (só ~78% das médias coincidem; 14.561 filmes têm avaliações sem
resumo). Por isso as avaliações individuais são a fonte da verdade: o resumo é recalculado
na carga e a cada avaliação criada ou excluída, na mesma transação.

**Limpeza dos dados**, feita na carga:

| Problema nos CSVs | Tratamento |
| --- | --- |
| Idiomas, países, gêneros e números cadastrados como pessoas ("English" dirigia 248 filmes) | 1.101 registros e seus vínculos removidos |
| 1.976 sinopses e 55 títulos com aspas duplicadas (`"texto ""citado"""`) | Desfeita a dupla serialização |
| Numerais romanos afetados por title-case (`Frozen Ii`) | Corrigidos (`Frozen II`) |
| Duração 0 em 10.160 filmes | Tratada como desconhecida (`NULL`) |
| "Lucro" falso em 8.039 filmes (−orçamento sem receita, ou a receita inteira sem orçamento) | A API só expõe o lucro quando há orçamento **e** receita |

Também comparei os CSVs com a camada gold do meu pipeline de engenharia de dados no
Databricks (mesmo dataset). Os CSVs fornecidos tinham o texto mais íntegro, então foram
mantidos, com a limpeza acima cobrindo os problemas que os dois tinham em comum.

**Outras regras.** `id_filme` é o id do TMDB nos CSVs; filmes cadastrados aqui recebem o
prefixo `rl-`. Diretores existentes são reaproveitados pelo nome (sem diferenciar
maiúsculas), e a edição troca só os diretores, preservando elenco e roteiro. A exclusão é
um único `DELETE`, com o `ON DELETE CASCADE` do banco removendo avaliações e vínculos.

**Limitações conhecidas.** Alguns "nomes" de pessoa ainda são fragmentos de frase vindos
da origem (~500 vínculos de 745 mil), e não foram removidos para não apagar nomes reais
longos. A carga completa leva cerca de 1 min 30 s (mais dentro de pastas sincronizadas, como o
OneDrive), porque confere as chaves estrangeiras linha a linha.
