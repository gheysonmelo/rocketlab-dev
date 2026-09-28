import sqlite3
from pathlib import Path

from sqlalchemy import create_engine

from app.db.base import Base
from app.movies import models  # noqa: F401  Registra os modelos ORM.
from app.scripts.seed import rebuild_review_summary


def create_schema(db_path: Path) -> None:
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    engine.dispose()


def test_rebuild_review_summary_uses_individual_reviews(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    create_schema(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executemany(
            "INSERT INTO dim_movies (sk_movie_id, id_filme, titulo) VALUES (?, ?, ?)",
            [("m-1", "1", "Com avaliações"), ("m-2", "2", "Sem avaliações")],
        )
        # Resumo antigo e errado, como o do dim_reviews.csv: deve ser descartado.
        connection.execute("INSERT INTO dim_reviews VALUES ('m-1', 'm-1', 5, 0.5)")
        connection.executemany(
            "INSERT INTO movie_reviews (sk_movie_review_id, sk_movie_id, nome, nota, comentario)"
            " VALUES (?, 'm-1', ?, ?, 'ok')",
            [("r-1", "Ana", 8.0), ("r-2", "Bia", 9.0)],
        )

        assert rebuild_review_summary(connection) == 1
        summary = connection.execute(
            "SELECT sk_review_id, sk_movie_id, qtd_avaliacoes_usuarios, nota_media_usuarios"
            " FROM dim_reviews"
        ).fetchall()

    # Só filmes com avaliação ganham resumo, com a média real: (8 + 9) / 2.
    assert summary == [("m-1", "m-1", 2, 8.5)]
