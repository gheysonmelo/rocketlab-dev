import httpx
import pytest

from app.core.config import get_settings


async def test_login_returns_token(client: httpx.AsyncClient) -> None:
    settings = get_settings()
    response = await client.post(
        "/auth/login",
        json={"username": settings.admin_username, "password": settings.admin_password},
    )

    assert response.status_code == 200
    token = response.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.json() == {"username": settings.admin_username}


async def test_login_rejects_wrong_password(client: httpx.AsyncClient) -> None:
    response = await client.post("/auth/login", json={"username": "admin", "password": "errada"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Usuário ou senha inválidos."}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/movies"),
        ("put", "/movies/m-oppenheimer"),
        ("delete", "/movies/m-oppenheimer"),
        ("post", "/movies/m-oppenheimer/reviews"),
        ("delete", "/movies/m-oppenheimer/reviews/r-1"),
    ],
)
async def test_write_routes_require_login(
    client: httpx.AsyncClient, method: str, path: str
) -> None:
    del client.headers["Authorization"]  # sem login

    response = await client.request(method, path, json={})

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


async def test_invalid_token_is_rejected(client: httpx.AsyncClient) -> None:
    client.headers["Authorization"] = "Bearer token-falso"

    response = await client.delete("/movies/m-oppenheimer")

    assert response.status_code == 401
    assert response.json() == {"detail": "Token inválido."}


async def test_reading_stays_public(client: httpx.AsyncClient) -> None:
    del client.headers["Authorization"]

    assert (await client.get("/movies")).status_code == 200
    assert (await client.get("/movies/m-oppenheimer")).status_code == 200
