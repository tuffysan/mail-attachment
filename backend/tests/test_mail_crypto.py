import pytest

from mailhub.mail.crypto import CredentialCipher


def test_cipher_round_trip() -> None:
    cipher = CredentialCipher("x" * 32)
    token = cipher.encrypt("secret password")
    assert token != "secret password"
    assert cipher.decrypt(token) == "secret password"


def test_cipher_rejects_other_key() -> None:
    token = CredentialCipher("a" * 32).encrypt("secret")
    with pytest.raises(ValueError):
        CredentialCipher("b" * 32).decrypt(token)
