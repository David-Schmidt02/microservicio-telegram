"""Modelo de dominio para Chat"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Chat:
    """Representa un chat de Telegram en el sistema"""

    chat_id: int
    title: Optional[str] = None
    type: str = "private"  # "private", "group", "supergroup", "channel"
    is_allowed: bool = False  # Por defecto no está en whitelist
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def is_group(self) -> bool:
        """Verifica si es un grupo"""
        return self.type in ("group", "supergroup")

    def is_private(self) -> bool:
        """Verifica si es un chat privado"""
        return self.type == "private"

    def get_display_name(self) -> str:
        """Retorna el nombre para mostrar del chat"""
        if self.title:
            return self.title
        elif self.is_private():
            return f"Chat privado {self.chat_id}"
        else:
            return f"Chat {self.chat_id}"

    def to_dict(self) -> dict:
        """Convierte el chat a diccionario (para serialización)"""
        return {
            "chat_id": self.chat_id,
            "title": self.title,
            "type": self.type,
            "is_allowed": self.is_allowed,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            "updated_at": self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Chat":
        """Crea un chat desde un diccionario"""
        # Convertir strings ISO a datetime si es necesario
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        return cls(
            chat_id=data["chat_id"],
            title=data.get("title"),
            type=data.get("type", "private"),
            is_allowed=data.get("is_allowed", False),
            created_at=created_at or datetime.now(),
            updated_at=updated_at or datetime.now(),
        )
