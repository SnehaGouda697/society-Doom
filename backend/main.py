"""FastAPI application and authenticated Strawberry GraphQL endpoint."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from backend.auth import user_from_access_token
from backend.database import SessionLocal, create_tables
from backend.schema import schema


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield


app = FastAPI(title="Society Doom API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://127.0.0.1:4200"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


async def get_context(request: Request) -> AsyncGenerator[dict, None]:
    """Open one database session per GraphQL request and resolve its user."""
    session = SessionLocal()
    try:
        authorization = request.headers.get("Authorization", "")
        scheme, _, token = authorization.partition(" ")
        token = token.strip() if scheme.lower() == "bearer" else None
        yield {"request": request, "session": session, "current_user": user_from_access_token(session, token)}
    finally:
        session.close()


app.include_router(GraphQLRouter(schema, context_getter=get_context), prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
