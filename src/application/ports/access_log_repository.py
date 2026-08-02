from abc import ABC, abstractmethod
from src.domain.login_event import LoginEvent

class AccessLogRepository(ABC):
    @abstractmethod
    def save(self,event:LoginEvent)->None:
        raise NotImplementedError


