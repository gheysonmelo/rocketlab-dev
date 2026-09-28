import httpx
import pytest


def titles(response: httpx.Response) -> list[str]:
    return [movie["titulo"] for movie in response.json()["items"]]


async def test_list_movies(client: httpx.AsyncClient) -> None:
    response = await client.get("/movies")

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["page"], body["pages"]) == (3, 1, 1)
    assert titles(response) == ["100% Wolf", "Dunkirk", "Oppenheimer"]

    wolf, dunkirk, oppenheimer = body["items"]
    assert oppenheimer["avaliacao"] == {"media": 8.8, "qtd_avaliacoes": 2}
    assert oppenheimer["url_poster"].endswith("oppenheimer.jpg")
    assert dunkirk["avaliacao"] == {"media": None, "qtd_avaliacoes": 0}

    # Gêneros em ordem alfabética; só diretores (o ator Cillian Murphy fica de fora).
    assert [g["nome_genero"] for g in oppenheimer["generos"]] == ["Drama", "History"]
    assert [d["nome_pessoa"] for d in oppenheimer["diretores"]] == ["Christopher Nolan"]
    assert [d["nome_pessoa"] for d in dunkirk["diretores"]] == ["Christopher Nolan"]
    assert (wolf["generos"], wolf["diretores"]) == ([], [])


async def test_list_movies_pagination(client: httpx.AsyncClient) -> None:
    response = await client.get("/movies", params={"page": 2, "page_size": 2})

    body = response.json()
    assert (body["total"], body["page"], body["page_size"], body["pages"]) == (3, 2, 2, 2)
    assert titles(response) == ["Oppenheimer"]


@pytest.mark.parametrize(
    ("q", "expected"),
    [
        ("oppen", ["Oppenheimer"]),
        ("  dunkirk  ", ["Dunkirk"]),
        ("100%", ["100% Wolf"]),
        ("%", ["100% Wolf"]),  # % é texto, não curinga: não pode devolver tudo
        ("_", []),
        ("inexistente", []),
    ],
)
async def test_search_by_title(client: httpx.AsyncClient, q: str, expected: list[str]) -> None:
    response = await client.get("/movies", params={"q": q})

    assert response.status_code == 200
    assert titles(response) == expected
    assert response.json()["total"] == len(expected)


@pytest.mark.parametrize("params", [{"page": 0}, {"page_size": 101}, {"q": ""}])
async def test_list_movies_rejects_invalid_params(client: httpx.AsyncClient, params: dict) -> None:
    response = await client.get("/movies", params=params)

    assert response.status_code == 422


async def test_list_genres(client: httpx.AsyncClient) -> None:
    response = await client.get("/genres")

    assert response.status_code == 200
    assert [g["nome_genero"] for g in response.json()] == ["Drama", "History"]


@pytest.mark.parametrize(
    ("params", "expected"),
    [
        ({"genero_id": "g-history"}, ["Oppenheimer"]),
        ({"genero_id": "g-drama"}, ["Dunkirk", "Oppenheimer"]),
        ({"ano": 2017}, ["Dunkirk"]),
        ({"status": "Lançado"}, ["Oppenheimer"]),
        ({"genero_id": "g-drama", "ano": 2023}, ["Oppenheimer"]),  # filtros combinados
        ({"q": "dunk", "genero_id": "g-history"}, []),
    ],
)
async def test_list_movies_filters(client: httpx.AsyncClient, params: dict, expected: list) -> None:
    response = await client.get("/movies", params=params)

    assert response.status_code == 200
    assert titles(response) == expected


async def test_list_movies_rejects_invalid_status(client: httpx.AsyncClient) -> None:
    assert (await client.get("/movies", params={"status": "Cancelado"})).status_code == 422
