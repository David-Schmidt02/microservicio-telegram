"""Modelo de dominio para Usuario"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Representa un usuario de Telegram en el sistema"""

    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_allowed: bool = False  # Por defecto no está en whitelist
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get_display_name(self) -> str:
        """Retorna el nombre para mostrar del usuario"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.username:
            return f"@{self.username}"
        else:
            return f"User#{self.user_id}"

    def to_dict(self) -> dict:
        """Convierte el usuario a diccionario (para serialización)"""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_allowed": self.is_allowed,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Crea un usuario desde un diccionario"""
        # Convertir strings ISO a datetime si es necesario
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            user_id=data["user_id"],
            username=data.get("username"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            is_allowed=data.get("is_allowed", False),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
        )
