"""Regras de negócio de escrita: filmes (cadastro, edição, exclusão) e avaliações."""

from hashlib import sha256
from uuid import uuid4

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import InvalidDataError, NotFoundError
from app.movies import repository
from app.movies.models import DimGenre, DimMovie, DimPerson, DimReview, MovieReview
from app.movies.schemas import DIRECTOR, MovieWrite, ReviewCreate


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


# ---------------------------------------------------------------------------
# Avaliações
# ---------------------------------------------------------------------------


async def _ensure_movie_exists(session: AsyncSession, movie_id: str) -> None:
    found = await session.scalar(
        select(DimMovie.sk_movie_id).where(DimMovie.sk_movie_id == movie_id)
    )
    if found is None:
        raise NotFoundError("Filme não encontrado.")


async def refresh_rating_summary(session: AsyncSession, movie_id: str) -> None:
    """Recalcula o resumo (dim_reviews) do filme a partir das avaliações individuais.

    Recalcular do zero, em vez de somar e subtrair, garante que o resumo nunca se
    desalinhe das avaliações. Sem avaliações, o resumo é apagado.
    """

    count, average = (
        await session.execute(
            select(func.count(), func.round(func.avg(MovieReview.nota), 2)).where(
                MovieReview.sk_movie_id == movie_id
            )
        )
    ).one()
    if count == 0:
        await session.execute(delete(DimReview).where(DimReview.sk_movie_id == movie_id))
        return
    # "Upsert": cria o resumo na primeira avaliação e atualiza nas seguintes.
    upsert = sqlite_insert(DimReview).values(
        sk_review_id=movie_id,  # convenção dos CSVs: sk_review_id = sk_movie_id
        sk_movie_id=movie_id,
        qtd_avaliacoes_usuarios=count,
        nota_media_usuarios=average,
    )
    await session.execute(
        upsert.on_conflict_do_update(
            index_elements=[DimReview.sk_movie_id],
            set_={
                "qtd_avaliacoes_usuarios": upsert.excluded.qtd_avaliacoes_usuarios,
                "nota_media_usuarios": upsert.excluded.nota_media_usuarios,
            },
        )
    )


async def list_reviews(
    session: AsyncSession, movie_id: str, offset: int, limit: int
) -> tuple[list[MovieReview], int]:
    await _ensure_movie_exists(session, movie_id)
    return await repository.list_reviews(session, movie_id, offset, limit)


async def create_review(session: AsyncSession, movie_id: str, data: ReviewCreate) -> MovieReview:
    await _ensure_movie_exists(session, movie_id)
    review = MovieReview(sk_movie_id=movie_id, **data.model_dump())
    session.add(review)
    await session.flush()  # grava a avaliação antes de recalcular a média
    await refresh_rating_summary(session, movie_id)
    await session.commit()  # avaliação e resumo entram juntos, ou nenhum dos dois
    await session.refresh(review)  # traz o created_at gerado pelo banco
    return review


async def delete_review(session: AsyncSession, movie_id: str, review_id: str) -> None:
    result = await session.execute(
        delete(MovieReview)
        .where(MovieReview.sk_movie_review_id == review_id)
        .where(MovieReview.sk_movie_id == movie_id)
    )
    if result.rowcount == 0:
        raise NotFoundError("Avaliação não encontrada.")
    await refresh_rating_summary(session, movie_id)
    await session.commit()
