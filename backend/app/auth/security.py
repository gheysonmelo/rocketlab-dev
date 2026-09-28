"""Emissão e validação de tokens JWT do administrador."""

import hmac
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings

ALGORITHM = "HS256"
bearer = HTTPBearer(auto_error=False)


def check_credentials(username: str, password: str) -> bool:
    settings = get_settings()
    # compare_digest evita ataques de tempo (a comparação não "vaza" onde difere).
    user_ok = hmac.compare_digest(username.encode(), settings.admin_username.encode())
    password_ok = hmac.compare_digest(password.encode(), settings.admin_password.encode())
    return user_ok and password_ok


def create_access_token(username: str) -> str:
    settings = get_settings()
    expires = datetime.now(UTC) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode({"sub": username, "exp": expires}, settings.jwt_secret, algorithm=ALGORITHM)


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"}
    )


def require_admin(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    """Dependência das rotas protegidas: exige um token válido e devolve o usuário."""

    if credentials is None:
        raise _unauthorized("Faça login para continuar.")
    try:
        payload = jwt.decode(
            credentials.credentials, get_settings().jwt_secret, algorithms=[ALGORITHM]
        )
    except jwt.ExpiredSignatureError as error:
        raise _unauthorized("Sessão expirada. Faça login novamente.") from error
    except jwt.InvalidTokenError as error:
        raise _unauthorized("Token inválido.") from error
    return payload["sub"]


AdminUser = Annotated[str, Depends(require_admin)]
