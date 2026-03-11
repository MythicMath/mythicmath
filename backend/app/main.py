from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from app.engine.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


app = FastAPI(title="MythicMath API", lifespan=lifespan)
app.include_router(api_router)
