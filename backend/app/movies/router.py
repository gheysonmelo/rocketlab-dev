"""Endpoints do catálogo de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import require_admin
from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams, page_params
from app.db.session import get_db
from app.movies import repository, service
from app.movies.schemas import (
    GenreRead,
    MovieDetail,
    MovieStatus,
    MovieSummary,
    MovieWrite,
    ReviewCreate,
    ReviewRead,
)

Session = Annotated[AsyncSession, Depends(get_db)]
# Leitura é pública; escrita (criar, editar, excluir, avaliar) exige login do administrador.
ADMIN = [Depends(require_admin)]

movies_router = APIRouter(prefix="/movies", tags=["movies"])
genres_router = APIRouter(prefix="/genres", tags=["genres"])


@genres_router.get("", response_model=list[GenreRead], summary="Gêneros disponíveis")
async def list_genres(session: Session) -> list[GenreRead]:
    return [GenreRead.model_validate(genre) for genre in await repository.list_genres(session)]


@movies_router.get("", response_model=Page[MovieSummary], summary="Catálogo paginado")
async def list_movies(
    session: Session,
    pagination: Annotated[PageParams, Depends(page_params)],
    q: Annotated[
        str | None, Query(min_length=1, max_length=100, description="Busca pelo título")
    ] = None,
    genero_id: Annotated[str | None, Query(description="Filtra por gênero")] = None,
    ano: Annotated[int | None, Query(ge=1870, le=2100, description="Ano de lançamento")] = None,
    status_filme: Annotated[
        MovieStatus | None, Query(alias="status", description="Status do filme")
    ] = None,
) -> Page[MovieSummary]:
    movies, total = await repository.list_movies(
        session,
        q.strip() if q else None,
        pagination.offset,
        pagination.page_size,
        genero_id=genero_id,
        ano=ano,
        status=status_filme,
    )
    return Page[MovieSummary].build(
        [MovieSummary.from_model(movie) for movie in movies], total, pagination
    )


NOT_FOUND = {404: {"description": "Filme não encontrado"}}


async def _detail_or_404(session: AsyncSession, movie_id: str) -> MovieDetail:
    movie = await repository.get_movie(session, movie_id)
    if movie is None:
        raise NotFoundError("Filme não encontrado.")
    return MovieDetail.from_model(movie)


@movies_router.get(
    "/{movie_id}",
    response_model=MovieDetail,
    summary="Ficha completa do filme",
    responses=NOT_FOUND,
)
async def get_movie(movie_id: str, session: Session) -> MovieDetail:
    return await _detail_or_404(session, movie_id)


@movies_router.post(
    "",
    dependencies=ADMIN,
    response_model=MovieDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastra um filme",
)
async def create_movie(data: MovieWrite, session: Session) -> MovieDetail:
    movie_id = await service.create_movie(session, data)
    return await _detail_or_404(session, movie_id)


@movies_router.put(
    "/{movie_id}",
    dependencies=ADMIN,
    response_model=MovieDetail,
    summary="Atualiza um filme",
    responses=NOT_FOUND,
)
async def update_movie(movie_id: str, data: MovieWrite, session: Session) -> MovieDetail:
    await service.update_movie(session, movie_id, data)
    return await _detail_or_404(session, movie_id)


@movies_router.delete(
    "/{movie_id}",
    dependencies=ADMIN,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um filme e suas avaliações",
    responses=NOT_FOUND,
)
async def delete_movie(movie_id: str, session: Session) -> Response:
    await service.delete_movie(session, movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@movies_router.get(
    "/{movie_id}/reviews",
    response_model=Page[ReviewRead],
    summary="Avaliações do filme (mais recentes primeiro)",
    responses=NOT_FOUND,
)
async def list_reviews(
    movie_id: str,
    session: Session,
    pagination: Annotated[PageParams, Depends(page_params)],
) -> Page[ReviewRead]:
    reviews, total = await service.list_reviews(
        session, movie_id, pagination.offset, pagination.page_size
    )
    return Page[ReviewRead].build(
        [ReviewRead.model_validate(review) for review in reviews], total, pagination
    )


@movies_router.post(
    "/{movie_id}/reviews",
    dependencies=ADMIN,
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona uma avaliação e recalcula a média",
    responses=NOT_FOUND,
)
async def create_review(movie_id: str, data: ReviewCreate, session: Session) -> ReviewRead:
    return ReviewRead.model_validate(await service.create_review(session, movie_id, data))


@movies_router.delete(
    "/{movie_id}/reviews/{review_id}",
    dependencies=ADMIN,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove uma avaliação e recalcula a média",
    responses={404: {"description": "Filme ou avaliação não encontrados"}},
)
async def delete_review(movie_id: str, review_id: str, session: Session) -> Response:
    await service.delete_review(session, movie_id, review_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
