"""Contratos (Pydantic) das respostas da API de filmes."""

from pydantic import BaseModel, ConfigDict

from app.movies.models import DimMovie

DIRECTOR = "Diretor"


class GenreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sk_genre_id: str
    nome_genero: str


class PersonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sk_person_id: str
    nome_pessoa: str
    tipo_pessoa: str


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
        directors = sorted(
            (person for person in movie.people if person.tipo_pessoa == DIRECTOR),
            key=lambda person: person.nome_pessoa,
        )
        return cls(
            sk_movie_id=movie.sk_movie_id,
            titulo=movie.titulo,
            ano_lancamento=movie.ano_lancamento,
            url_poster=movie.url_poster,
            generos=[GenreRead.model_validate(genre) for genre in movie.genres],
            diretores=[PersonRead.model_validate(person) for person in directors],
            avaliacao=RatingSummary(
                media=summary.nota_media_usuarios if summary else None,
                qtd_avaliacoes=summary.qtd_avaliacoes_usuarios if summary else 0,
            ),
        )
