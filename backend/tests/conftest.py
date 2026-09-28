from collections.abc import AsyncIterator
from pathlib import Path

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.movies.models import DimGenre, DimMovie, DimPerson, DimReview


def sample_movies() -> list[DimMovie]:
    """Três filmes: um com resumo de avaliações e um com % no título (teste do LIKE).

    Nolan dirige dois deles; Cillian Murphy é ator e não pode aparecer como diretor.
    """

    drama = DimGenre(sk_genre_id="g-drama", nome_genero="Drama")
    history = DimGenre(sk_genre_id="g-history", nome_genero="History")
    nolan = DimPerson(
        sk_person_id="p-nolan", nome_pessoa="Christopher Nolan", tipo_pessoa="Diretor"
    )
    murphy = DimPerson(sk_person_id="p-murphy", nome_pessoa="Cillian Murphy", tipo_pessoa="Ator")

    return [
        DimMovie(
            sk_movie_id="m-oppenheimer",
            id_filme="872585",
            titulo="Oppenheimer",
            ano_lancamento=2023,
            url_poster="https://image.tmdb.org/t/p/w500/oppenheimer.jpg",
            genres=[history, drama],
            people=[murphy, nolan],
            reviews_summary=DimReview(
                sk_review_id="m-oppenheimer", qtd_avaliacoes_usuarios=2, nota_media_usuarios=8.8
            ),
        ),
        DimMovie(
            sk_movie_id="m-dunkirk",
            id_filme="374720",
            titulo="Dunkirk",
            ano_lancamento=2017,
            genres=[drama],
            people=[nolan],
        ),
        DimMovie(sk_movie_id="m-wolf", id_filme="525662", titulo="100% Wolf", ano_lancamento=2020),
    ]


@pytest.fixture
async def client(tmp_path: Path) -> AsyncIterator[httpx.AsyncClient]:
    """Cliente HTTP da API usando um SQLite temporário, em vez do rocketlab.db."""

    engine = create_async_engine(f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}")
    enable_sqlite_foreign_keys(engine)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    sessions = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with sessions() as session:
        session.add_all(sample_movies())
        await session.commit()

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test/api/v1") as http:
        yield http
    app.dependency_overrides.clear()
    await engine.dispose()
