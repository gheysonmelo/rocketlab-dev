"""Paginação reutilizável pelos endpoints de listagem."""

from dataclasses import dataclass
from math import ceil
from typing import Annotated, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


@dataclass(frozen=True)
class PageParams:
    page: int
    page_size: int

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def page_params(
    page: Annotated[int, Query(ge=1, description="Página, começando em 1")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Itens por página")] = 24,
) -> PageParams:
    """Dependência do FastAPI: lê e valida ``page`` e ``page_size`` da query string."""

    return PageParams(page=page, page_size=page_size)


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    pages: int

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams) -> "Page[T]":
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            pages=ceil(total / params.page_size),
        )
