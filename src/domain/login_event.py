from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class LoginEvent:
    username:str
    attempted_at:datetime
    success:bool
    message:str
    source:str = "streamlit"


