"""Erros de regra de negócio e sua conversão em respostas HTTP.

A camada de serviço levanta estes erros sem saber nada de HTTP; o handler
registrado no app transforma cada um no status e na mensagem corretos.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class DomainError(Exception):
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    status_code = 404


class InvalidDataError(DomainError):
    status_code = 422


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        del request
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
