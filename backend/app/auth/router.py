from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.auth.security import AdminUser, check_credentials, create_access_token

auth_router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@auth_router.post("/login", response_model=TokenResponse, summary="Login do administrador")
async def login(data: LoginRequest) -> TokenResponse:
    if not check_credentials(data.username, data.password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos.")
    return TokenResponse(access_token=create_access_token(data.username))


@auth_router.get("/me", summary="Usuário autenticado")
async def me(user: AdminUser) -> dict[str, str]:
    return {"username": user}
