from abc import ABC, abstractmethod
from src.domain.access_log import LoginEvent

class AccessLogRepository(ABC):
    @abstractmethod
    def save(self,event:LoginEvent)->None:
        raise NotImplementedError


