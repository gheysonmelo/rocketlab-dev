"""Endpoints do catálogo de filmes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pagination import Page, PageParams, page_params
from app.db.session import get_db
from app.movies import repository
from app.movies.schemas import MovieDetail, MovieSummary

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


@movies_router.get(
    "/{movie_id}",
    response_model=MovieDetail,
    summary="Ficha completa do filme",
    responses={404: {"description": "Filme não encontrado"}},
)
async def get_movie(movie_id: str, session: Session) -> MovieDetail:
    movie = await repository.get_movie(session, movie_id)
    if movie is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Filme não encontrado.")
    return MovieDetail.from_model(movie)
