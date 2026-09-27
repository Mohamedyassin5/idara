"""
Authentication
==============

Account creation and login with JWT (HS256).

- POST /auth/register  {name, email, password}  -> {access_token, user}
- POST /auth/login     {email, password}        -> {access_token, user}
- GET  /auth/me        (Bearer token)           -> user

Users live in the same database as the rest of the app: Postgres (Neon) when DATABASE_URL is set,
otherwise a local SQLite file (db/users.db). Passwords are hashed with scrypt (standard library).
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from functools import cache
from os import getenv
from pathlib import Path

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, select
from sqlalchemy.exc import IntegrityError

from db.url import db_url

JWT_ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=int(getenv("AUTH_TOKEN_HOURS", "12")))

# Paths that need a valid token. Everything else (docs, health, /auth/*) stays public.
PROTECTED_PREFIXES = ("/teams", "/agents", "/workflows", "/sessions", "/memory")


def _secret() -> str:
    secret = getenv("AUTH_JWT_SECRET")
    if secret:
        return secret
    if getenv("RUNTIME_ENV", "prd") == "prd":
        raise RuntimeError("AUTH_JWT_SECRET must be set in production")
    return "dev-only-insecure-secret-change-me-32bytes!"  # local development only


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------
metadata = MetaData()
users = Table(
    "app_users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(255), unique=True, nullable=False, index=True),
    Column("name", String(120), nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


@cache
def _engine():
    url = db_url if getenv("DATABASE_URL") else f"sqlite:///{Path(__file__).parent.parent / 'db' / 'users.db'}"
    engine = create_engine(url, pool_pre_ping=True)
    metadata.create_all(engine)
    return engine


# ---------------------------------------------------------------------------
# Passwords and tokens
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt_hex), n=2**14, r=8, p=1)
        return hmac.compare_digest(digest.hex(), digest_hex)
    except ValueError:
        return False


def create_token(user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {"sub": str(user_id), "email": email, "iat": now, "exp": now + TOKEN_TTL}
    return jwt.encode(payload, _secret(), algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _secret(), algorithms=[JWT_ALGORITHM])


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
class RegisterBody(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginBody(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


def _public(row) -> dict:
    return {"id": row.id, "name": row.name, "email": row.email}


def current_user(request: Request) -> dict:
    header = request.headers.get("authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        claims = decode_token(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    with _engine().connect() as conn:
        row = conn.execute(select(users).where(users.c.id == int(claims["sub"]))).first()
    if row is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return _public(row)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(body: RegisterBody) -> dict:
    email = body.email.lower()
    try:
        with _engine().begin() as conn:
            result = conn.execute(
                users.insert().values(
                    email=email,
                    name=body.name.strip(),
                    password_hash=hash_password(body.password),
                    created_at=datetime.now(timezone.utc),
                )
            )
            user_id = result.inserted_primary_key[0]
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Email already registered")
    return {
        "access_token": create_token(user_id, email),
        "user": {"id": user_id, "name": body.name.strip(), "email": email},
    }


@router.post("/login")
def login(body: LoginBody) -> dict:
    email = body.email.lower()
    with _engine().connect() as conn:
        row = conn.execute(select(users).where(users.c.email == email)).first()
    if row is None or not verify_password(body.password, row.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return {"access_token": create_token(row.id, row.email), "user": _public(row)}


@router.get("/me")
def me(user: dict = Depends(current_user)) -> dict:
    return user


async def auth_middleware(request: Request, call_next):
    """Require a valid Bearer token on the agent endpoints (CORS preflight passes through)."""
    path = request.url.path
    if request.method != "OPTIONS" and path.startswith(PROTECTED_PREFIXES):
        header = request.headers.get("authorization", "")
        token = header.partition(" ")[2]
        try:
            decode_token(token)
        except jwt.PyJWTError:
            return JSONResponse({"detail": "Authentication required"}, status_code=401)
    return await call_next(request)
