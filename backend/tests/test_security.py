from uuid import uuid4

from mailhub.auth.security import create_access_token, decode_access_token, hash_password, verify_password
from mailhub.config import Settings


def settings() -> Settings:
    return Settings(app_secret_key="x" * 32, database_url="postgresql+asyncpg://u:p@localhost/db")


def test_password_hash_roundtrip() -> None:
    value = hash_password("correct-horse-battery-staple")
    assert verify_password("correct-horse-battery-staple", value)
    assert not verify_password("wrong-password", value)


def test_access_token_roundtrip() -> None:
    user_id = uuid4()
    token = create_access_token(user_id, settings())
    assert decode_access_token(token, settings()) == user_id
