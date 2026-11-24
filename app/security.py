import os
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_secret_key():
    secret_key = os.getenv("SECRET_KEY")

    if not secret_key:
        raise RuntimeError("SECRET_KEY is missing from .env file")

    return secret_key


def hash_password(password: str) -> str:
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            hashed.encode("utf-8")
        )
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        get_secret_key(),
        algorithm=ALGORITHM
    )


def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            get_secret_key(),
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None