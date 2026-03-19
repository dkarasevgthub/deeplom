from contextlib import asynccontextmanager

from fastapi import FastAPI

from auth.router import router as auth_router
from config import get_settings
from db import close_db_pool, initialize_db_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_db_pool(settings)
    try:
        yield
    finally:
        close_db_pool()


app = FastAPI(title="Golangmonster API", lifespan=lifespan)


@app.get("/")
def root():
    return "Hello, World!"

@app.get("/health")
def root():
    return {"status": "ok"}


app.include_router(auth_router)
