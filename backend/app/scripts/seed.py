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
from pathlib import Path

from sqlalchemy.engine import make_url

from app.core.config import get_settings

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
    ("dim_reviews", "dim_reviews.csv"),
    # Atenção: o arquivo se chama "movies_reviews", mas a tabela é "movie_reviews".
    ("movie_reviews", "movies_reviews.csv"),
]


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
    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
    # executemany envia todas as linhas num só comando preparado: bem mais rápido
    # do que um INSERT por linha.
    connection.executemany(sql, rows)
    return len(rows)


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
                for table, _ in reversed(LOAD_ORDER):
                    connection.execute(f"DELETE FROM {table}")
            for table, _ in LOAD_ORDER:
                started = time.perf_counter()
                count = load_table(connection, table, files[table])
                print(f"{table:<25} {count:>9,} linhas  {time.perf_counter() - started:5.1f}s")
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
