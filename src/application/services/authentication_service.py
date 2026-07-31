from datetime import datetime

from src.application.ports.access_log_repository import AccessLogRepository
from src.application.ports.password_hasher import PasswordHasher
from src.application.ports.user_repository import UserRepository
from src.domain.access_log import LoginEvent
from src.domain.users import AuthenticatedUser

class AuthenticationError(Exception):
    pass

class AuthenticationService:
    def __init__(
            self,
            user_repository:UserRepository,
            password_hasher:PasswordHasher,
            access_log_repository:AccessLogRepository,
        ) -> None:
        self._user_repository=user_repository
        self._password_hasher=password_hasher
        self._access_log_repository=access_log_repository

    def login(self,username:str,password:str)-> AuthenticatedUser:
        normalized_username=username.strip().lower()
        attempted_at=datetime.now()

        user=self._user_repository.find_by_username(normalized_username)

        if user is None:
            self._register_failed_attempt(
                    username=normalized_username,
                    attempted_at=attempted_at,
                    message="Invalid credentials",
                )
            raise AuthenticationError("Credenciales Invalidas.")
        password_is_valid = self._password_hasher.verify_password(
                plain_password=password,
                password_hash=user.password_hash,
            )

        if not password_is_valid:
            self._register_failed_attempt(
                    username=normalized_username,
                    attempted_at=attempted_at,
                    message="Invalid credentials",
                )
            raise AuthenticationError("Credenciales Invalidas.")
        authenticated_user=AuthenticatedUser(
                username=user.username,
                full_name=user.full_name,
                role=user.role,
                authenticated_at=attempted_at,
            )
        self._access_log_repository.save(
                LoginEvent(
                    username=user.username,
                    attempted_at=attempted_at,
                    success=True,
                    message="Login successful",
                )
            )
        return authenticated_user


    def _register_failed_attempt(
            self,
            username:str,
            attempted_at:datetime,
            message:str,
        ) -> None:
        self._access_log_repository.save(
                LoginEvent(
                    username=username,
                    attempted_at=attempted_at,
                    success=False,
                    message=message,
                )
            )
