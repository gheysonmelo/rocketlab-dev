"""Endpoints do catálogo de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.pagination import Page, PageParams, page_params
from app.db.session import get_db
from app.movies import repository, service
from app.movies.schemas import MovieDetail, MovieSummary, MovieWrite

Session = Annotated[AsyncSession, Depends(get_db)]

movies_router = APIRouter(prefix="/movies", tags=["movies"])


@movies_router.get("", response_model=Page[MovieSummary], summary="Catálogo paginado")
async def list_movies(
    session: Session,
    pagination: Annotated[PageParams, Depends(page_params)],
    q: Annotated[
        str | None, Query(min_length=1, max_length=100, description="Busca pelo título")
    ] = None,
) -> Page[MovieSummary]:
    movies, total = await repository.list_movies(
        session, q.strip() if q else None, pagination.offset, pagination.page_size
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
    "", response_model=MovieDetail, status_code=status.HTTP_201_CREATED, summary="Cadastra um filme"
)
async def create_movie(data: MovieWrite, session: Session) -> MovieDetail:
    movie_id = await service.create_movie(session, data)
    return await _detail_or_404(session, movie_id)


@movies_router.put(
    "/{movie_id}", response_model=MovieDetail, summary="Atualiza um filme", responses=NOT_FOUND
)
async def update_movie(movie_id: str, data: MovieWrite, session: Session) -> MovieDetail:
    await service.update_movie(session, movie_id, data)
    return await _detail_or_404(session, movie_id)


@movies_router.delete(
    "/{movie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove um filme e suas avaliações",
    responses=NOT_FOUND,
)
async def delete_movie(movie_id: str, session: Session) -> Response:
    await service.delete_movie(session, movie_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
