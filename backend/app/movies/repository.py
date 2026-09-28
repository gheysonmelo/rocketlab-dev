"""Consultas ao banco do domínio de filmes.

No SQLAlchemy assíncrono não existe lazy loading: todo relacionamento usado
na resposta precisa ser carregado na própria consulta (``selectinload``).
"""

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.movies.models import DimMovie, DimPerson
from app.movies.schemas import DIRECTOR


def _like_pattern(term: str) -> str:
    """Busca por "contém", tratando % e _ digitados pelo usuário como texto."""

    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _apply_search(stmt: Select, q: str | None) -> Select:
    if q:
        stmt = stmt.where(DimMovie.titulo.like(_like_pattern(q), escape="\\"))
    return stmt


async def list_movies(
    session: AsyncSession, q: str | None, offset: int, limit: int
) -> tuple[list[DimMovie], int]:
    """Uma página do catálogo e o total de filmes que atendem à busca."""

    total = (
        await session.execute(_apply_search(select(func.count(DimMovie.sk_movie_id)), q))
    ).scalar_one()

    stmt = (
        _apply_search(select(DimMovie), q)
        .options(
            selectinload(DimMovie.reviews_summary),
            selectinload(DimMovie.genres),
            # Do elenco e da equipe, o card só precisa dos diretores.
            selectinload(DimMovie.people.and_(DimPerson.tipo_pessoa == DIRECTOR)),
        )
        # Ordem explícita e com desempate: sem isso a paginação pode repetir ou pular filmes.
        .order_by(DimMovie.titulo, DimMovie.sk_movie_id)
        .offset(offset)
        .limit(limit)
    )
    movies = (await session.scalars(stmt)).all()
    return list(movies), total


async def get_movie(session: AsyncSession, movie_id: str) -> DimMovie | None:
    """Filme com todos os relacionamentos que a ficha exibe, ou None se não existir."""

    stmt = (
        select(DimMovie)
        .where(DimMovie.sk_movie_id == movie_id)
        .options(
            selectinload(DimMovie.reviews_summary),
            selectinload(DimMovie.genres),
            selectinload(DimMovie.people),  # todas: diretores, roteiristas e elenco
            selectinload(DimMovie.companies),
            selectinload(DimMovie.performance),
        )
        # Relê do banco mesmo que o filme já esteja na sessão (ex.: logo após uma edição).
        .execution_options(populate_existing=True)
    )
    return (await session.scalars(stmt)).one_or_none()
