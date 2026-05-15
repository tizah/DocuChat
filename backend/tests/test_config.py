"""Guardrails on the Settings model."""

import pytest
from pydantic import ValidationError

from app.config import DEFAULT_JWT_SECRET, Settings


def test_default_jwt_secret_rejected_in_prod():
    """Booting with debug=False and the placeholder secret must fail."""
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY is set to the placeholder"):
        Settings(debug=False, jwt_secret_key=DEFAULT_JWT_SECRET)


def test_default_jwt_secret_allowed_in_debug():
    """Local dev (debug=true) is allowed to use the placeholder."""
    s = Settings(debug=True, jwt_secret_key=DEFAULT_JWT_SECRET)
    assert s.jwt_secret_key == DEFAULT_JWT_SECRET


def test_custom_jwt_secret_in_prod_is_fine():
    s = Settings(debug=False, jwt_secret_key="a-real-secret-with-enough-entropy-for-prod")
    assert s.debug is False
