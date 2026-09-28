"""Contratos (Pydantic) das respostas da API de filmes."""

from datetime import date
from decimal import Decimal
from typing import Annotated, Any, Literal

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    HttpUrl,
    StringConstraints,
    UrlConstraints,
    field_validator,
    model_validator,
)

from app.movies.models import DimMovie, FactMoviePerformance

DIRECTOR = "Diretor"
WRITER = "Roteirista"
ACTOR = "Ator"


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sk_genre_id: str
    nome_genero: str


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sk_person_id: str
    nome_pessoa: str
    tipo_pessoa: str


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sk_company_id: str
    nome_produtora: str


def people_by_role(movie: DimMovie, role: str) -> list[PersonRead]:
    """Pessoas do filme com o papel pedido, em ordem alfabética."""

    people = sorted(
        (person for person in movie.people if person.tipo_pessoa == role),
        key=lambda person: person.nome_pessoa,
    )
    return [PersonRead.model_validate(person) for person in people]


class RatingSummary(BaseModel):
    """Média na escala do banco (0 a 10); o frontend converte para estrelas (÷ 2)."""

    media: float | None
    qtd_avaliacoes: int


class MovieSummary(BaseModel):
    """Um filme no catálogo."""

    sk_movie_id: str
    titulo: str
    ano_lancamento: int | None
    url_poster: str | None
    generos: list[GenreRead]
    diretores: list[PersonRead]
    avaliacao: RatingSummary

    @classmethod
    def from_model(cls, movie: DimMovie) -> "MovieSummary":
        summary = movie.reviews_summary
        return cls(
            sk_movie_id=movie.sk_movie_id,
            titulo=movie.titulo,
            ano_lancamento=movie.ano_lancamento,
            url_poster=movie.url_poster,
            generos=[GenreRead.model_validate(genre) for genre in movie.genres],
            diretores=people_by_role(movie, DIRECTOR),
            avaliacao=RatingSummary(
                media=summary.nota_media_usuarios if summary else None,
                qtd_avaliacoes=summary.qtd_avaliacoes_usuarios if summary else 0,
            ),
        )


def _money(value: Decimal | None) -> float | None:
    # A coluna é Numeric: o banco devolve Decimal, que viraria texto no JSON.
    return float(value) if value is not None else None


class PerformanceRead(BaseModel):
    """Desempenho financeiro e notas externas do filme.

    Nos CSVs, o lucro vira ``-orçamento`` quando falta a receita e ``receita``
    quando falta o orçamento (8.039 filmes). Por isso ele só é exposto quando
    orçamento e receita existem.
    """

    orcamento_usd: float | None
    receita_usd: float | None
    lucro_usd: float | None
    orcamento_brl: float | None
    receita_brl: float | None
    lucro_brl: float | None
    popularidade: float | None
    nota_tmdb: float | None
    qtd_tmdb: int | None
    nota_imdb: float | None
    qtd_imdb: int | None

    @classmethod
    def from_model(cls, fact: FactMoviePerformance) -> "PerformanceRead":
        has_usd = fact.orcamento_usd is not None and fact.receita_usd is not None
        has_brl = fact.orcamento_brl is not None and fact.receita_brl is not None
        return cls(
            orcamento_usd=_money(fact.orcamento_usd),
            receita_usd=_money(fact.receita_usd),
            lucro_usd=_money(fact.lucro_usd) if has_usd else None,
            orcamento_brl=_money(fact.orcamento_brl),
            receita_brl=_money(fact.receita_brl),
            lucro_brl=_money(fact.lucro_brl) if has_brl else None,
            popularidade=fact.popularidade,
            nota_tmdb=fact.nota_tmdb,
            qtd_tmdb=fact.qtd_tmdb,
            nota_imdb=fact.nota_imdb,
            qtd_imdb=fact.qtd_imdb,
        )


class MovieDetail(MovieSummary):
    """Ficha completa: o que o catálogo mostra mais o restante do filme."""

    id_filme: str
    data_lancamento: date | None
    duracao_minutos: int | None
    status_filme: str | None
    sinopse: str | None
    url_backdrop: str | None
    roteiristas: list[PersonRead]
    elenco: list[PersonRead]
    produtoras: list[CompanyRead]
    desempenho: PerformanceRead | None

    @classmethod
    def from_model(cls, movie: DimMovie) -> "MovieDetail":
        return cls(
            **MovieSummary.from_model(movie).model_dump(),
            id_filme=movie.id_filme,
            data_lancamento=movie.data_lancamento,
            duracao_minutos=movie.duracao_minutos,
            status_filme=movie.status_filme,
            sinopse=movie.sinopse,
            url_backdrop=movie.url_backdrop,
            roteiristas=people_by_role(movie, WRITER),
            elenco=people_by_role(movie, ACTOR),
            produtoras=[CompanyRead.model_validate(company) for company in movie.companies],
            desempenho=PerformanceRead.from_model(movie.performance) if movie.performance else None,
        )


# ---------------------------------------------------------------------------
# Entrada: cadastro e edição
# ---------------------------------------------------------------------------

MovieStatus = Literal["Lançado", "Pós-Produção", "Em Produção", "Planejado"]


def _blank_to_none(value: Any) -> Any:
    """Campo opcional enviado vazio ("") é tratado como não informado."""

    return None if isinstance(value, str) and not value.strip() else value


Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
OptionalText = Annotated[
    Annotated[str, StringConstraints(strip_whitespace=True, max_length=4000)] | None,
    BeforeValidator(_blank_to_none),
]
OptionalUrl = Annotated[
    Annotated[HttpUrl, UrlConstraints(max_length=2048)] | None,
    BeforeValidator(_blank_to_none),
]


class MovieWrite(BaseModel):
    """Dados para cadastrar (POST) ou substituir (PUT) um filme."""

    # Campo desconhecido é erro: pega de cara um nome digitado errado no front.
    model_config = ConfigDict(extra="forbid")

    titulo: Title
    diretores: list[PersonName] = Field(default_factory=list, max_length=10)
    genero_ids: list[str] = Field(default_factory=list, max_length=19)
    data_lancamento: date | None = None
    ano_lancamento: int | None = Field(default=None, ge=1870, le=2100)
    duracao_minutos: int | None = Field(default=None, ge=1, le=20000)
    status_filme: MovieStatus = "Lançado"
    sinopse: OptionalText = None
    url_poster: OptionalUrl = None
    url_backdrop: OptionalUrl = None

    @field_validator("diretores", "genero_ids")
    @classmethod
    def _without_duplicates(cls, values: list[str]) -> list[str]:
        """Remove repetições (sem diferenciar maiúsculas), mantendo a ordem."""

        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            if value.casefold() not in seen:
                seen.add(value.casefold())
                unique.append(value)
        return unique

    @model_validator(mode="after")
    def _year_matches_date(self) -> "MovieWrite":
        if self.data_lancamento is None:
            return self
        if self.ano_lancamento is None:
            self.ano_lancamento = self.data_lancamento.year
        elif self.ano_lancamento != self.data_lancamento.year:
            raise ValueError("ano_lancamento deve ser o mesmo ano de data_lancamento.")
        return self
