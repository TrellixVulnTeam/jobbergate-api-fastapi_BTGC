"""
Instantiates armasec resources for auth on api endpoints using project settings.

Also provides a factory function for TokenSecurity to reduce boilerplate.
"""
from typing import Optional

from armasec import Armasec, TokenPayload
from loguru import logger
from pydantic import BaseModel, EmailStr

from jobbergate_api.config import settings

guard = Armasec(
    settings.ARMASEC_DOMAIN,
    audience=settings.ARMASEC_AUDIENCE,
    debug_logger=logger.debug if settings.ARMASEC_DEBUG else None,
)


class IdentityClaims(BaseModel):
    """
    Provide a pydantic data model containing user data extracted from an access token.
    """

    email: Optional[EmailStr]
    client_id: Optional[str]

    @classmethod
    def from_token_payload(cls, payload: TokenPayload) -> "IdentityClaims":
        """
        Create an instance from a Token payload.

        Automatically validates that the email is an email address if it is provided.
        """
        return cls(
            email=getattr(payload, "email"),
            client_id=payload.client_id,
        )
