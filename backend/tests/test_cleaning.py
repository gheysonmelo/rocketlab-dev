import sqlite3
from pathlib import Path

import pytest
from sqlalchemy import create_engine

from app.db.base import Base
from app.movies import models  # noqa: F401  Registra os modelos ORM.
from app.scripts.cleaning import (
    clean_movie,
    fix_roman_numerals,
    is_not_a_person,
    unwrap_double_quoted,
)
from app.scripts.seed import remove_placeholder_people


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('"Julia sees a ""movie within the movie""."', 'Julia sees a "movie within the movie".'),
        ('"From the makers of ""FantastiCozzi""', 'From the makers of "FantastiCozzi"'),
        ('"Only wrapped"', "Only wrapped"),
        # Citação legítima: não mexe.
        ('"Plus Ultra" is the motto of Spain.', '"Plus Ultra" is the motto of Spain.'),
        ("No quotes at all", "No quotes at all"),
        (None, None),
    ],
)
def test_unwrap_double_quoted(raw: str | None, expected: str | None) -> None:
    assert unwrap_double_quoted(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Frozen Ii", "Frozen II"),
        ("Boyka: Undisputed Iv", "Boyka: Undisputed IV"),
        ("Rocky Iii: The Return", "Rocky III: The Return"),
        ("Iiyama Stories", "Iiyama Stories"),
        ("Vi Er Hjemme", "Vi Er Hjemme"),
    ],
)
def test_fix_roman_numerals(raw: str, expected: str) -> None:
    assert fix_roman_numerals(raw) == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("English", True),
        ("United States Of America", True),
        ("Documentary", True),
        ("Short Film", True),
        ("0.6", True),
        ("Christopher Nolan", False),
        ("Sukumar", False),
        ("宮崎駿", False),
        ("Jordan Peele", False),
    ],
)
def test_is_not_a_person(name: str, expected: bool) -> None:
    assert is_not_a_person(name) is expected


def test_clean_movie() -> None:
    row = {"titulo": "Frozen Ii", "sinopse": '"Uma ""aventura""."', "duracao_minutos": "0"}

    assert clean_movie(row) == {
        "titulo": "Frozen II",
        "sinopse": 'Uma "aventura".',
        "duracao_minutos": None,
    }


def test_remove_placeholder_people(tmp_path: Path) -> None:
    db_path = tmp_path / "test.db"
    engine = create_engine(f"sqlite:///{db_path.as_posix()}")
    Base.metadata.create_all(engine)
    engine.dispose()

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute(
            "INSERT INTO dim_movies (sk_movie_id, id_filme, titulo) VALUES ('m', '1', 'X')"
        )
        connection.executemany(
            "INSERT INTO dim_people (sk_person_id, nome_pessoa, tipo_pessoa) VALUES (?, ?, ?)",
            [("p-ana", "Ana Diretora", "Diretor"), ("p-en", "English", "Diretor")],
        )
        connection.executemany(
            "INSERT INTO bridge_movie_person (sk_movie_id, sk_person_id) VALUES ('m', ?)",
            [("p-ana",), ("p-en",)],
        )

        assert remove_placeholder_people(connection) == 1
        people = connection.execute("SELECT nome_pessoa FROM dim_people").fetchall()
        links = connection.execute("SELECT sk_person_id FROM bridge_movie_person").fetchall()

    assert people == [("Ana Diretora",)]
    assert links == [("p-ana",)]
