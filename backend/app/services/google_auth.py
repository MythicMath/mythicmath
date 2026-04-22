import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi.concurrency import run_in_threadpool
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token


class GoogleAuthConfigError(RuntimeError):
    pass


class GoogleAuthError(ValueError):
    pass


@dataclass(frozen=True)
class GoogleIdentity:
    subject: str
    email: str
    name: str
    picture: Optional[str] = None


def _configured_client_ids() -> List[str]:
    raw_values = [
        os.getenv("GOOGLE_CLIENT_IDS", ""),
        os.getenv("GOOGLE_CLIENT_ID", ""),
    ]

    client_ids: List[str] = []
    for raw_value in raw_values:
        client_ids.extend(
            client_id.strip()
            for client_id in raw_value.split(",")
            if client_id.strip()
        )

    return list(dict.fromkeys(client_ids))


def _is_email_verified(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def _verify_google_id_token_sync(
    token: str, client_ids: List[str]
) -> Dict[str, Any]:
    request = requests.Request()
    last_error: Optional[Exception] = None

    for client_id in client_ids:
        try:
            return google_id_token.verify_oauth2_token(token, request, client_id)
        except ValueError as exc:
            last_error = exc

    raise GoogleAuthError("Invalid Google ID token") from last_error


async def verify_google_id_token(token: str) -> GoogleIdentity:
    client_ids = _configured_client_ids()
    if not client_ids:
        raise GoogleAuthConfigError("GOOGLE_CLIENT_IDS is not configured")

    payload = await run_in_threadpool(_verify_google_id_token_sync, token, client_ids)

    if not _is_email_verified(payload.get("email_verified")):
        raise GoogleAuthError("Google email is not verified")

    subject = payload.get("sub")
    email = payload.get("email")
    if not subject or not email:
        raise GoogleAuthError("Google ID token is missing required claims")

    email_value = str(email).lower()
    picture = payload.get("picture")

    return GoogleIdentity(
        subject=str(subject),
        email=email_value,
        name=str(payload.get("name") or email_value.split("@", 1)[0]),
        picture=str(picture) if picture else None,
    )
