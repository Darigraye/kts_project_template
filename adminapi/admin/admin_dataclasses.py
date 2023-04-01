from hashlib import sha256
from typing import Optional
from dataclasses import dataclass


@dataclass
class Admin:
    login: str
    password: Optional[str] = None

    def is_password_valid(self, password: str):
        return self.password == sha256(password.encode()).hexdigest()

    @classmethod
    def from_session(cls, session: Optional[dict]) -> Optional["Admin"]:
        return cls(login=session["admin"]["login"])
