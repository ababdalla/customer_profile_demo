import base64
import hashlib
import hmac
import os


class Pbkdf2PasswordHasher:
    def __init__(self, iterations: int = 390_000) -> None:
        self._iterations = iterations

    def hash_password(self, plain_password: str) -> str:
        salt = os.urandom(16)
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            self._iterations,
        )

        encoded_salt = base64.b64encode(salt).decode("utf-8")
        encoded_hash = base64.b64encode(password_hash).decode("utf-8")

        return f"pbkdf2_sha256${self._iterations}${encoded_salt}${encoded_hash}"

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        algorithm, iterations, encoded_salt, encoded_expected_hash = password_hash.split("$")

        if algorithm != "pbkdf2_sha256":
            return False

        salt = base64.b64decode(encoded_salt)
        expected_hash = base64.b64decode(encoded_expected_hash)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(calculated_hash, expected_hash)
