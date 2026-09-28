import httpx
import pytest

NEW_MOVIE = {
    "titulo": "  Tenet  ",
    "diretores": ["christopher nolan", "Nova Diretora"],
    "genero_ids": ["g-drama"],
    "data_lancamento": "2020-08-26",
    "duracao_minutos": 150,
    "sinopse": "Um agente manipula o fluxo do tempo.",
    "url_poster": "https://image.tmdb.org/t/p/w500/tenet.jpg",
}


async def test_create_movie(client: httpx.AsyncClient) -> None:
    response = await client.post("/movies", json=NEW_MOVIE)

    assert response.status_code == 201
    movie = response.json()
    assert movie["titulo"] == "Tenet"  # espaços das pontas removidos
    assert movie["id_filme"].startswith("rl-")
    assert movie["ano_lancamento"] == 2020  # derivado da data
    assert movie["status_filme"] == "Lançado"  # padrão
    assert [g["nome_genero"] for g in movie["generos"]] == ["Drama"]
    assert movie["avaliacao"] == {"media": None, "qtd_avaliacoes": 0}

    # "christopher nolan" reaproveita o diretor existente; "Nova Diretora" é criada.
    directors = {d["nome_pessoa"]: d["sk_person_id"] for d in movie["diretores"]}
    assert directors["Christopher Nolan"] == "p-nolan"
    assert set(directors) == {"Christopher Nolan", "Nova Diretora"}

    catalog = (await client.get("/movies")).json()
    assert catalog["total"] == 4
    assert (await client.get(f"/movies/{movie['sk_movie_id']}")).status_code == 200


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"titulo": "   "}, "titulo"),
        ({"ano_lancamento": 2019}, "ano_lancamento"),  # diferente do ano da data
        ({"duracao_minutos": 0}, "duracao_minutos"),
        ({"status_filme": "Cancelado"}, "status_filme"),
        ({"url_poster": "nao-e-url"}, "url_poster"),
        ({"campo_inexistente": 1}, "campo_inexistente"),
    ],
)
async def test_create_movie_validation(client: httpx.AsyncClient, change: dict, field: str) -> None:
    response = await client.post("/movies", json={**NEW_MOVIE, **change})

    assert response.status_code == 422
    assert field in str(response.json()["detail"])


async def test_create_movie_with_unknown_genre(client: httpx.AsyncClient) -> None:
    response = await client.post("/movies", json={**NEW_MOVIE, "genero_ids": ["g-nao-existe"]})

    assert response.status_code == 422
    assert response.json() == {"detail": "Gênero(s) inexistente(s): g-nao-existe."}


async def test_update_movie_replaces_directors_and_keeps_cast(client: httpx.AsyncClient) -> None:
    payload = {
        "titulo": "Oppenheimer (2023)",
        "diretores": ["Outra Pessoa"],
        "genero_ids": ["g-history"],
        "ano_lancamento": 2023,
        "sinopse": "",
    }
    response = await client.put("/movies/m-oppenheimer", json=payload)

    assert response.status_code == 200
    movie = response.json()
    assert movie["titulo"] == "Oppenheimer (2023)"
    assert [d["nome_pessoa"] for d in movie["diretores"]] == ["Outra Pessoa"]
    assert [g["nome_genero"] for g in movie["generos"]] == ["History"]
    assert movie["sinopse"] is None  # "" vira não informado
    # O formulário não tem elenco nem roteiro: eles continuam lá.
    assert [p["nome_pessoa"] for p in movie["elenco"]] == ["Cillian Murphy"]
    assert [p["nome_pessoa"] for p in movie["roteiristas"]] == ["Christopher Nolan"]
    assert movie["avaliacao"]["qtd_avaliacoes"] == 2


async def test_delete_movie(client: httpx.AsyncClient) -> None:
    # Oppenheimer tem avaliação, resumo, desempenho e vínculos: com as FKs ligadas,
    # o 204 só acontece se o CASCADE remover tudo junto.
    response = await client.delete("/movies/m-oppenheimer")

    assert response.status_code == 204
    assert (await client.get("/movies/m-oppenheimer")).status_code == 404
    assert (await client.get("/movies")).json()["total"] == 2
    # Nolan continua existindo: ele também dirige Dunkirk.
    dunkirk = (await client.get("/movies/m-dunkirk")).json()
    assert [d["nome_pessoa"] for d in dunkirk["diretores"]] == ["Christopher Nolan"]


@pytest.mark.parametrize("method", ["put", "delete"])
async def test_write_missing_movie(client: httpx.AsyncClient, method: str) -> None:
    kwargs = {"json": {"titulo": "X"}} if method == "put" else {}
    response = await getattr(client, method)("/movies/nao-existe", **kwargs)

    assert response.status_code == 404
    assert response.json() == {"detail": "Filme não encontrado."}
