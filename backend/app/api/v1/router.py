from fastapi import APIRouter

from app.auth.router import auth_router
from app.movies.router import genres_router, movies_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(movies_router)
api_router.include_router(genres_router)
