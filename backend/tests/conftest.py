from collections.abc import AsyncIterator
from datetime import date
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.auth.security import create_access_token
from app.db.base import Base
from app.db.session import enable_sqlite_foreign_keys, get_db
from app.main import app
from app.movies.models import (
    DimCompany,
    DimGenre,
    DimMovie,
    DimPerson,
    DimReview,
    FactMoviePerformance,
    MovieReview,
)


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
    nolan_writer = DimPerson(
        sk_person_id="p-nolan-w", nome_pessoa="Christopher Nolan", tipo_pessoa="Roteirista"
    )
    universal = DimCompany(sk_company_id="c-universal", nome_produtora="Universal Pictures")

    return [
        DimMovie(
            sk_movie_id="m-oppenheimer",
            id_filme="872585",
            titulo="Oppenheimer",
            ano_lancamento=2023,
            url_poster="https://image.tmdb.org/t/p/w500/oppenheimer.jpg",
            data_lancamento=date(2023, 7, 19),
            duracao_minutos=181,
            status_filme="Lançado",
            sinopse="The story of J. Robert Oppenheimer.",
            genres=[history, drama],
            people=[murphy, nolan, nolan_writer],
            companies=[universal],
            performance=FactMoviePerformance(
                orcamento_usd=Decimal("100000000.00"),
                receita_usd=Decimal("975000000.00"),
                lucro_usd=Decimal("875000000.00"),
                lucro_brl=Decimal("0"),
                popularidade=80.5,
                nota_tmdb=8.1,
                qtd_tmdb=9000,
            ),
            reviews=[
                MovieReview(sk_movie_review_id="r-1", nome="Ana", nota=9.0, comentario="Ótimo.")
            ],
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
            # Como nos CSVs: sem receita, o "lucro" vem como -orçamento.
            performance=FactMoviePerformance(
                orcamento_usd=Decimal("100000000.00"),
                lucro_usd=Decimal("-100000000.00"),
                lucro_brl=Decimal("0"),
            ),
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
    # Por padrão o cliente age como administrador logado (rotas de escrita exigem token).
    headers = {"Authorization": f"Bearer {create_access_token('admin')}"}
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test/api/v1", headers=headers
    ) as http:
        yield http
    app.dependency_overrides.clear()
    await engine.dispose()
