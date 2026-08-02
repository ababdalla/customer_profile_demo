from abc import ABC, abstractmethod
from typing import Optional

from src.domain.user import User

class UserRepository(ABC):
    @abstractmethod
    def find_by_username(self,username:str) -> Optional[User]:
        raise NotImplementedError
