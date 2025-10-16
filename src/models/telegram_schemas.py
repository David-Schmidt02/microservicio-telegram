from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TelegramUser(BaseModel):
    """Modelo para usuario de Telegram"""
    user_id: int
    username: Optional[str] = None
    user_first_name: str
    user_last_name: Optional[str] = None
    user_full_name: str
    user_language_code: Optional[str] = None
    is_bot: bool = False

    def get_display_name(self) -> str:
        """Retorna el nombre para mostrar (username o nombre completo)"""
        return self.username if self.username else self.user_full_name

    @classmethod
    def from_telegram_data(cls, from_data: dict) -> 'TelegramUser':
        """Crea un usuario desde los datos de Telegram API"""
        full_name = from_data.get("first_name", "")
        if from_data.get("last_name"):
            full_name += f" {from_data.get('last_name')}"

        return cls(
            user_id=from_data.get("id"),
            username=from_data.get("username"),
            user_first_name=from_data.get("first_name", "Unknown"),
            user_last_name=from_data.get("last_name"),
            user_full_name=full_name,
            user_language_code=from_data.get("language_code"),
            is_bot=from_data.get("is_bot", False)
        )


class TelegramChat(BaseModel):
    """Modelo para chat/grupo de Telegram"""
    chat_id: int
    chat_type: str  # "private", "group", "supergroup", "channel"
    chat_title: Optional[str] = None

    @classmethod
    def from_telegram_data(cls, chat_data: dict) -> 'TelegramChat':
        """Crea un chat desde los datos de Telegram API"""
        return cls(
            chat_id=chat_data.get("id"),
            chat_type=chat_data.get("type", "unknown"),
            chat_title=chat_data.get("title")
        )


class TelegramBaseMessage(BaseModel):
    """Modelo base para mensajes de Telegram"""
    update_id: int
    message_id: int
    date: int
    user: TelegramUser
    chat: TelegramChat

    class Config:
        # Permite campos extra sin error
        extra = 'ignore'


class TelegramTextMessage(TelegramBaseMessage):
    """Modelo para mensajes de texto"""
    text: str

    @classmethod
    def from_telegram_update(cls, update: dict) -> 'TelegramTextMessage':
        """Crea un mensaje de texto desde un update de Telegram"""
        message = update.get("message", {})

        return cls(
            update_id=update["update_id"],
            message_id=message["message_id"],
            text=message["text"],
            date=message.get("date"),
            user=TelegramUser.from_telegram_data(message.get("from", {})),
            chat=TelegramChat.from_telegram_data(message.get("chat", {}))
        )

    def to_dict(self) -> dict:
        """Convierte el mensaje a diccionario (compatibilidad con código existente)"""
        return {
            "update_id": self.update_id,
            "message_id": self.message_id,
            "text": self.text,
            "date": self.date,
            "chat_id": self.chat.chat_id,
            "chat_type": self.chat.chat_type,
            "chat_title": self.chat.chat_title,
            "user_id": self.user.user_id,
            "username": self.user.username,
            "user_first_name": self.user.user_first_name,
            "user_last_name": self.user.user_last_name,
            "user_full_name": self.user.user_full_name,
            "user_language_code": self.user.user_language_code,
            "is_bot": self.user.is_bot
        }


class TelegramAudioMessage(TelegramBaseMessage):
    """Modelo para mensajes de audio/voz"""
    file_id: str
    duration: Optional[int] = None

    @classmethod
    def from_telegram_update(cls, update: dict) -> 'TelegramAudioMessage':
        """Crea un mensaje de audio desde un update de Telegram"""
        message = update.get("message", {})
        audio_info = message.get("voice") or message.get("audio")

        return cls(
            update_id=update["update_id"],
            message_id=message["message_id"],
            file_id=audio_info["file_id"],
            duration=audio_info.get("duration"),
            date=message.get("date"),
            user=TelegramUser.from_telegram_data(message.get("from", {})),
            chat=TelegramChat.from_telegram_data(message.get("chat", {}))
        )

    def to_dict(self) -> dict:
        """Convierte el mensaje a diccionario (compatibilidad con código existente)"""
        return {
            "update_id": self.update_id,
            "message_id": self.message_id,
            "file_id": self.file_id,
            "duration": self.duration,
            "date": self.date,
            "chat_id": self.chat.chat_id,
            "chat_type": self.chat.chat_type,
            "chat_title": self.chat.chat_title,
            "user_id": self.user.user_id,
            "username": self.user.username,
            "user_first_name": self.user.user_first_name,
            "user_last_name": self.user.user_last_name,
            "user_full_name": self.user.user_full_name,
            "user_language_code": self.user.user_language_code,
            "is_bot": self.user.is_bot
        }
