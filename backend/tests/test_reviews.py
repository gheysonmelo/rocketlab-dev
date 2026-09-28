import httpx
import pytest

REVIEW = {"nome": "  Bia  ", "nota": 8, "comentario": "Muito bom."}


async def rating(client: httpx.AsyncClient, movie_id: str) -> dict:
    return (await client.get(f"/movies/{movie_id}")).json()["avaliacao"]


async def test_list_reviews(client: httpx.AsyncClient) -> None:
    response = await client.get("/movies/m-oppenheimer/reviews")

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["pages"]) == (1, 1)
    review = body["items"][0]
    assert (review["nome"], review["nota"], review["comentario"]) == ("Ana", 9.0, "Ótimo.")
    assert review["created_at"].endswith("Z")  # UTC explícito para o front


async def test_create_review_recalculates_average(client: httpx.AsyncClient) -> None:
    # O resumo de teste diz "2 avaliações, média 8,8", mas só existe uma avaliação (9).
    response = await client.post("/movies/m-oppenheimer/reviews", json=REVIEW)

    assert response.status_code == 201
    review = response.json()
    assert (review["nome"], review["nota"]) == ("Bia", 8.0)
    # Recalculado das avaliações reais: (9 + 8) / 2 = 8,5 com 2 avaliações.
    assert await rating(client, "m-oppenheimer") == {"media": 8.5, "qtd_avaliacoes": 2}
    # A mais recente vem primeiro.
    listed = (await client.get("/movies/m-oppenheimer/reviews")).json()["items"]
    assert [r["nome"] for r in listed] == ["Bia", "Ana"]


async def test_first_review_creates_summary(client: httpx.AsyncClient) -> None:
    assert await rating(client, "m-dunkirk") == {"media": None, "qtd_avaliacoes": 0}

    await client.post("/movies/m-dunkirk/reviews", json={**REVIEW, "nota": 10})

    assert await rating(client, "m-dunkirk") == {"media": 10.0, "qtd_avaliacoes": 1}
    # A média nova também aparece no catálogo.
    catalog = (await client.get("/movies", params={"q": "dunkirk"})).json()
    assert catalog["items"][0]["avaliacao"] == {"media": 10.0, "qtd_avaliacoes": 1}


@pytest.mark.parametrize(
    "change",
    [
        {"nota": 0},
        {"nota": 11},
        {"nota": 7.5},  # não corresponde a nenhuma meia estrela
        {"nome": "   "},
        {"comentario": ""},
        {"extra": True},
    ],
)
async def test_create_review_validation(client: httpx.AsyncClient, change: dict) -> None:
    response = await client.post("/movies/m-oppenheimer/reviews", json={**REVIEW, **change})

    assert response.status_code == 422


async def test_delete_reviews_until_empty(client: httpx.AsyncClient) -> None:
    created = (await client.post("/movies/m-oppenheimer/reviews", json=REVIEW)).json()

    assert (await client.delete("/movies/m-oppenheimer/reviews/r-1")).status_code == 204
    assert await rating(client, "m-oppenheimer") == {"media": 8.0, "qtd_avaliacoes": 1}

    await client.delete(f"/movies/m-oppenheimer/reviews/{created['sk_movie_review_id']}")
    assert await rating(client, "m-oppenheimer") == {"media": None, "qtd_avaliacoes": 0}


async def test_reviews_not_found(client: httpx.AsyncClient) -> None:
    assert (await client.get("/movies/nao-existe/reviews")).status_code == 404
    assert (await client.post("/movies/nao-existe/reviews", json=REVIEW)).status_code == 404

    response = await client.delete("/movies/m-oppenheimer/reviews/nao-existe")
    assert response.status_code == 404
    assert response.json() == {"detail": "Avaliação não encontrada."}
