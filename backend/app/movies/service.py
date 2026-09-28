"""Regras de negócio de escrita do catálogo (cadastro, edição e exclusão)."""

from hashlib import sha256
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import InvalidDataError, NotFoundError
from app.movies.models import DimGenre, DimMovie, DimPerson
from app.movies.schemas import DIRECTOR, MovieWrite


def _sha256(text: str) -> str:
    return sha256(text.encode()).hexdigest()


def new_external_id() -> str:
    """id_filme é o id do TMDB nos CSVs; filmes cadastrados aqui ganham prefixo próprio."""

    return f"rl-{uuid4().hex[:12]}"


async def _resolve_genres(session: AsyncSession, genre_ids: list[str]) -> list[DimGenre]:
    if not genre_ids:
        return []
    genres = (
        await session.scalars(select(DimGenre).where(DimGenre.sk_genre_id.in_(genre_ids)))
    ).all()
    missing = set(genre_ids) - {genre.sk_genre_id for genre in genres}
    if missing:
        raise InvalidDataError(f"Gênero(s) inexistente(s): {', '.join(sorted(missing))}.")
    return list(genres)


async def _resolve_directors(session: AsyncSession, names: list[str]) -> list[DimPerson]:
    """Reaproveita diretores já cadastrados (sem diferenciar maiúsculas) ou cria novos."""

    if not names:
        return []
    existing = (
        await session.scalars(
            select(DimPerson)
            .where(DimPerson.tipo_pessoa == DIRECTOR)
            .where(DimPerson.nome_pessoa.collate("NOCASE").in_(names))
        )
    ).all()
    by_name = {person.nome_pessoa.casefold(): person for person in existing}
    return [
        by_name.get(name.casefold())
        # Mesma receita de chave dos CSVs: sha256(nome|tipo).
        or DimPerson(
            sk_person_id=_sha256(f"{name}|{DIRECTOR}"), nome_pessoa=name, tipo_pessoa=DIRECTOR
        )
        for name in names
    ]


async def _apply(session: AsyncSession, movie: DimMovie, data: MovieWrite) -> None:
    """Copia os dados do formulário para o filme (usado no cadastro e na edição)."""

    movie.titulo = data.titulo
    movie.data_lancamento = data.data_lancamento
    movie.ano_lancamento = data.ano_lancamento
    movie.duracao_minutos = data.duracao_minutos
    movie.status_filme = data.status_filme
    movie.sinopse = data.sinopse
    movie.url_poster = str(data.url_poster) if data.url_poster else None
    movie.url_backdrop = str(data.url_backdrop) if data.url_backdrop else None
    movie.genres = await _resolve_genres(session, data.genero_ids)
    # O formulário só tem diretores: elenco e roteiristas vindos dos CSVs são preservados.
    others = [person for person in movie.people if person.tipo_pessoa != DIRECTOR]
    movie.people = others + await _resolve_directors(session, data.diretores)


async def create_movie(session: AsyncSession, data: MovieWrite) -> str:
    external_id = new_external_id()
    # Mesma receita de chave dos CSVs: sha256(id_filme).
    movie = DimMovie(sk_movie_id=_sha256(external_id), id_filme=external_id)
    await _apply(session, movie, data)
    session.add(movie)
    await session.commit()
    return movie.sk_movie_id


async def update_movie(session: AsyncSession, movie_id: str, data: MovieWrite) -> None:
    movie = (
        await session.scalars(
            select(DimMovie)
            .where(DimMovie.sk_movie_id == movie_id)
            .options(selectinload(DimMovie.genres), selectinload(DimMovie.people))
        )
    ).one_or_none()
    if movie is None:
        raise NotFoundError("Filme não encontrado.")
    await _apply(session, movie, data)
    await session.commit()


async def delete_movie(session: AsyncSession, movie_id: str) -> None:
    # Um único DELETE: o ON DELETE CASCADE do banco remove avaliações, resumo,
    # desempenho e vínculos. As pessoas e gêneros ficam (podem estar em outros filmes).
    result = await session.execute(delete(DimMovie).where(DimMovie.sk_movie_id == movie_id))
    if result.rowcount == 0:
        raise NotFoundError("Filme não encontrado.")
    await session.commit()
