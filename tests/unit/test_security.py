"""Unit tests for password hashing and JWT security functions."""

import uuid
import pytest
from app.core.security import create_access_token, decode_token, get_password_hash, verify_password


def test_password_hashing():
    raw_password = "SecurePassword123!"
    hashed = get_password_hash(raw_password)
    
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_decoding():
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, extra_claims={"role": "BACHELOR"})
    
    decoded = decode_token(token)
    assert decoded["sub"] == str(user_id)
    assert decoded["type"] == "access"
    assert decoded["role"] == "BACHELOR"
