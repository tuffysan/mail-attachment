import json

from mailhub.mail.crypto import CredentialCipher


def encrypt_config(secret: str, config: dict[str, str]) -> str:
    normalized = {key: str(value) for key, value in config.items() if value is not None}
    return CredentialCipher(secret).encrypt(json.dumps(normalized, separators=(",", ":")))


def decrypt_config(secret: str, encrypted: str | None) -> dict[str, str]:
    if not encrypted:
        return {}
    return json.loads(CredentialCipher(secret).decrypt(encrypted))
