import hashlib
import secrets
from datetime import UTC, datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

PASSWORD_MIN_LENGTH = 14
PASSWORD_MAX_LENGTH = 256
_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)
_dummy_hash = _hasher.hash("civicsignal-dummy-password-never-used")


def normalize_identifier(value: str) -> str:
    return value.strip().casefold()


def validate_password(value: str) -> None:
    if not PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH:
        raise ValueError(
            f"Password must contain {PASSWORD_MIN_LENGTH} to {PASSWORD_MAX_LENGTH} characters"
        )
    if value.casefold() in {"passwordpassword", "civicsignalcivicsignal"}:
        raise ValueError("Password is too easily guessed")


def hash_password(value: str) -> str:
    validate_password(value)
    return _hasher.hash(value)


def verify_password(stored_hash: str | None, candidate: str) -> tuple[bool, str | None]:
    target = stored_hash or _dummy_hash
    try:
        valid: bool = _hasher.verify(target, candidate[:PASSWORD_MAX_LENGTH])
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        valid = False
    if not stored_hash or not valid:
        return False, None
    return True, _hasher.hash(candidate) if _hasher.check_needs_rehash(stored_hash) else None


def new_secret() -> str:
    return secrets.token_urlsafe(48)


def secret_hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def utcnow() -> datetime:
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)
