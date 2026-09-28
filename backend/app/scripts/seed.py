"""Carga inicial dos CSVs da atividade no SQLite.

Uso (dentro de ``backend/``, depois de ``alembic upgrade head``)::

    python -m app.scripts.seed                          # CSVs na raiz do repositório
    python -m app.scripts.seed --data-dir C:/meus/csvs  # CSVs em outra pasta
    python -m app.scripts.seed --reset                  # apaga os dados e recarrega
"""

import argparse
import csv
import sqlite3
import sys
import time
from collections.abc import Callable
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import get_settings
from app.scripts.cleaning import clean_movie, is_not_a_person

# backend/app/scripts/seed.py -> raiz do repositório
REPO_ROOT = Path(__file__).resolve().parents[3]
IGNORED_DIRS = {".git", ".venv", "venv", "node_modules"}

# (tabela, arquivo CSV) na ordem das chaves estrangeiras: uma tabela só é
# carregada depois das tabelas que ela referencia.
LOAD_ORDER = [
    ("dim_genres", "dim_genres.csv"),
    ("dim_companies", "dim_companies.csv"),
    ("dim_people", "dim_people.csv"),
    ("dim_movies", "dim_movies.csv"),
    ("bridge_movie_genre", "bridge_movie_genre.csv"),
    ("bridge_movie_company", "bridge_movie_company.csv"),
    ("bridge_movie_person", "bridge_movie_person.csv"),
    ("fact_movies_performance", "fact_movies_performance.csv"),
    # Atenção: o arquivo se chama "movies_reviews", mas a tabela é "movie_reviews".
    ("movie_reviews", "movies_reviews.csv"),
    # dim_reviews.csv não é carregado: o resumo não bate com as avaliações individuais
    # (só ~78% das médias coincidem), então ele é recalculado (rebuild_review_summary).
]

Row = dict[str, str | None]

# Limpeza aplicada linha a linha antes do INSERT (ver app/scripts/cleaning.py).
CLEANERS: dict[str, Callable[[Row], Row]] = {
    "dim_movies": clean_movie,
}


def find_csv(data_dir: Path, filename: str) -> Path:
    """Procura o CSV em ``data_dir`` e subpastas (ex.: ``bases_atv_dev1/``)."""

    for path in data_dir.rglob(filename):
        if not IGNORED_DIRS.intersection(path.relative_to(data_dir).parts):
            return path
    raise FileNotFoundError(f"{filename} não encontrado em {data_dir}. Use --data-dir.")


def database_path() -> Path:
    """Caminho do arquivo SQLite a partir do DATABASE_URL do .env."""

    url = make_url(get_settings().database_url)
    if not url.drivername.startswith("sqlite") or not url.database:
        raise ValueError(f"A carga só suporta SQLite em arquivo: {url}")
    return Path(url.database)


def read_csv(path: Path) -> tuple[list[str], list[list[str | None]]]:
    """Lê o CSV inteiro; campo vazio vira None (NULL no banco)."""

    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        columns = next(reader)
        rows = [[value if value != "" else None for value in row] for row in reader]
    return columns, rows


def load_table(connection: sqlite3.Connection, table: str, path: Path) -> int:
    columns, rows = read_csv(path)
    cleaner = CLEANERS.get(table)
    if cleaner:
        cleaned = (cleaner(dict(zip(columns, row, strict=True))) for row in rows)
        rows = [[row[column] for column in columns] for row in cleaned]
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    # executemany envia todas as linhas num só comando preparado: bem mais rápido
    # do que um INSERT por linha.
    connection.executemany(sql, rows)
    return len(rows)


def remove_placeholder_people(connection: sqlite3.Connection) -> int:
    """Apaga "pessoas" que são idiomas, países, gêneros ou números, e seus vínculos."""

    people = connection.execute("SELECT sk_person_id, nome_pessoa FROM dim_people")
    ids = [(person_id,) for person_id, name in people if is_not_a_person(name)]
    # Vínculos primeiro: com as FKs ligadas, a pessoa não pode sumir antes deles.
    connection.executemany("DELETE FROM bridge_movie_person WHERE sk_person_id = ?", ids)
    connection.executemany("DELETE FROM dim_people WHERE sk_person_id = ?", ids)
    return len(ids)


def rebuild_review_summary(connection: sqlite3.Connection) -> int:
    """Preenche dim_reviews (quantidade e média por filme) a partir de movie_reviews.

    As avaliações individuais são a fonte da verdade; o resumo é derivado delas.
    Segue a convenção dos CSVs: sk_review_id é igual ao sk_movie_id.
    """

    connection.execute("DELETE FROM dim_reviews")
    connection.execute(
        """
        INSERT INTO dim_reviews
            (sk_review_id, sk_movie_id, qtd_avaliacoes_usuarios, nota_media_usuarios)
        SELECT sk_movie_id, sk_movie_id, COUNT(*), ROUND(AVG(nota), 2)
        FROM movie_reviews
        GROUP BY sk_movie_id
        """
    )
    return connection.execute("SELECT COUNT(*) FROM dim_reviews").fetchone()[0]


def seed(db_path: Path, data_dir: Path, reset: bool) -> None:
    files = {table: find_csv(data_dir, filename) for table, filename in LOAD_ORDER}

    connection = sqlite3.connect(db_path)
    try:
        # O SQLite vem com as FKs desligadas; ligamos para a carga acusar erros de ordem.
        connection.execute("PRAGMA foreign_keys = ON")

        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master")}
        if "dim_movies" not in tables:
            raise RuntimeError("Tabelas não encontradas. Rode `alembic upgrade head` antes.")

        existing = connection.execute("SELECT COUNT(*) FROM dim_movies").fetchone()[0]
        if existing and not reset:
            raise RuntimeError(f"O banco já tem {existing} filmes. Use --reset para recarregar.")

        # "with connection" abre uma única transação: ou tudo entra, ou nada entra.
        with connection:
            if reset:
                connection.execute("DELETE FROM dim_reviews")
                for table, _ in reversed(LOAD_ORDER):
                    connection.execute(f"DELETE FROM {table}")
            for table, _ in LOAD_ORDER:
                started = time.perf_counter()
                count = load_table(connection, table, files[table])
                print(f"{table:<25} {count:>9,} linhas  {time.perf_counter() - started:5.1f}s")
            removed = remove_placeholder_people(connection)
            print(f"{'dim_people':<25} {removed:>9,} removidas (idiomas, países, gêneros...)")
            summaries = rebuild_review_summary(connection)
            print(f"{'dim_reviews':<25} {summaries:>9,} resumos recalculados das avaliações")
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Carrega os CSVs da atividade no SQLite.")
    parser.add_argument("--data-dir", type=Path, default=REPO_ROOT, help="Pasta com os CSVs.")
    parser.add_argument("--reset", action="store_true", help="Apaga os dados antes de carregar.")
    args = parser.parse_args()

    started = time.perf_counter()
    try:
        seed(database_path(), args.data_dir.resolve(), args.reset)
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"Erro: {error}", file=sys.stderr)
        return 1
    print(f"Carga concluída em {time.perf_counter() - started:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
