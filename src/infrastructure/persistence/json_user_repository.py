import json
from pathlib import Path
from typing import Optional

from src.application.ports.user_repository import UserRepository
from src.domain.users import User

class JsonUserRepository(UserRepository):
    def __init__(self,file_path:Path)->None:
        self._file_path=file_path

    def find_by_username(self, username:str) -> Optional[User]:
        users=self._load_users()

        for user_data in users:
                if user_data["username"].lower()==username.lower():
                    return User(
                            username=user_data["username"],
                            full_name=user_data["full_name"],
                            role=user_data["role"],
                            password_hash=user_data["password_hash"],
                            is_active=user_data.get("is_active",True),
                        )
        return None

    def _load_users(self)-> list[dict]:
        if not self._file_path.exists():
            return[]

        with self._file_path.open("r", encoding="utf-8") as file:
            return json.load(file)



