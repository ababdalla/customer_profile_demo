from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class User:
    username:str
    full_name:str
    role:str
    password_hash:str
    is_active:bool=True

@dataclass(frozen=True)
class AuthenticatedUser:
    username:str
    full_name:str
    role:str
    authenticated_at:datetime


