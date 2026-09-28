import httpx


async def test_movie_detail(client: httpx.AsyncClient) -> None:
    response = await client.get("/movies/m-oppenheimer")

    assert response.status_code == 200
    movie = response.json()
    assert movie["titulo"] == "Oppenheimer"
    assert (movie["id_filme"], movie["data_lancamento"], movie["duracao_minutos"]) == (
        "872585",
        "2023-07-19",
        181,
    )
    assert movie["sinopse"] == "The story of J. Robert Oppenheimer."
    assert movie["avaliacao"] == {"media": 8.8, "qtd_avaliacoes": 2}
    assert [g["nome_genero"] for g in movie["generos"]] == ["Drama", "History"]
    # Cada pessoa aparece só no papel dela.
    assert [p["nome_pessoa"] for p in movie["diretores"]] == ["Christopher Nolan"]
    assert [p["nome_pessoa"] for p in movie["roteiristas"]] == ["Christopher Nolan"]
    assert [p["nome_pessoa"] for p in movie["elenco"]] == ["Cillian Murphy"]
    assert [c["nome_produtora"] for c in movie["produtoras"]] == ["Universal Pictures"]


async def test_movie_detail_performance(client: httpx.AsyncClient) -> None:
    performance = (await client.get("/movies/m-oppenheimer")).json()["desempenho"]

    assert performance["orcamento_usd"] == 100_000_000.0
    assert performance["receita_usd"] == 975_000_000.0
    assert performance["lucro_usd"] == 875_000_000.0
    assert (performance["nota_tmdb"], performance["qtd_tmdb"]) == (8.1, 9000)


async def test_profit_is_hidden_without_revenue(client: httpx.AsyncClient) -> None:
    performance = (await client.get("/movies/m-dunkirk")).json()["desempenho"]

    assert performance["orcamento_usd"] == 100_000_000.0
    assert performance["receita_usd"] is None
    # O CSV traz -100 mi, que não é lucro de verdade: fica null.
    assert performance["lucro_usd"] is None


async def test_movie_without_performance_or_relations(client: httpx.AsyncClient) -> None:
    movie = (await client.get("/movies/m-wolf")).json()

    assert movie["desempenho"] is None
    assert movie["elenco"] == movie["roteiristas"] == movie["produtoras"] == []


async def test_movie_detail_not_found(client: httpx.AsyncClient) -> None:
    response = await client.get("/movies/nao-existe")

    assert response.status_code == 404
    assert response.json() == {"detail": "Filme não encontrado."}
