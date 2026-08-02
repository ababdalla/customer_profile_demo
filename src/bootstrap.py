from pathlib import Path

from src.application.use_cases.login_user import AuthenticationService
from src.infrastructure.persistence.csv_access_log_repository import CsvAccessLogRepository
from src.infrastructure.persistence.json_user_repository import JsonUserRepository
from src.infrastructure.security.pbkdf2_password_hasher import Pbkdf2PasswordHasher


def build_authentication_service() -> AuthenticationService:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    user_repository = JsonUserRepository(data_dir / "users.json")
    access_log_repository = CsvAccessLogRepository(data_dir / "access_log.csv")
    password_hasher = Pbkdf2PasswordHasher()

    return AuthenticationService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        access_log_repository=access_log_repository,
    )
