"""Servicio de autorización para validar usuarios y chats"""
from src.repositories.user_repository import UserRepository
from src.repositories.chat_repository import ChatRepository
from src.models.user import User
from src.models.chat import Chat
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AuthorizationService:
    """Servicio que maneja la lógica de whitelist para usuarios y chats"""

    def __init__(
        self,
        user_repository: UserRepository = None,
        chat_repository: ChatRepository = None
    ):
        self.user_repo = user_repository or UserRepository()
        self.chat_repo = chat_repository or ChatRepository()

    def is_user_allowed(self, user_id: int) -> bool:
        """Valida si un usuario está en la whitelist"""
        user = self.user_repo.get_by_id(user_id)

        if not user:
            logger.warning(f"Usuario {user_id} no existe en la whitelist")
            return False

        if not user.is_allowed:
            logger.warning(f"Usuario {user_id} ({user.get_display_name()}) no está autorizado")
            return False

        logger.debug(f"Usuario {user_id} ({user.get_display_name()}) autorizado")
        return True

    def is_chat_allowed(self, chat_id: int) -> bool:
        """Valida si un chat está en la whitelist"""
        chat = self.chat_repo.get_by_id(chat_id)

        if not chat:
            logger.warning(f"Chat {chat_id} no existe en la whitelist")
            return False

        if not chat.is_allowed:
            logger.warning(f"Chat {chat_id} ({chat.get_display_name()}) no está autorizado")
            return False

        logger.debug(f"Chat {chat_id} ({chat.get_display_name()}) autorizado")
        return True

    def is_message_allowed(self, user_id: int, chat_id: int) -> bool:
        """Valida si un mensaje está autorizado (usuario Y chat en whitelist)"""
        user_allowed = self.is_user_allowed(user_id)
        chat_allowed = self.is_chat_allowed(chat_id)

        if not user_allowed:
            logger.info(f"Mensaje rechazado: usuario {user_id} no autorizado")
            return False

        if not chat_allowed:
            logger.info(f"Mensaje rechazado: chat {chat_id} no autorizado")
            return False

        return True

    def register_user_from_telegram(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        auto_allow: bool = False
    ) -> User:
        """Registra un usuario nuevo desde datos de Telegram"""
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_allowed=auto_allow
        )
        self.user_repo.save(user)
        logger.info(f"Usuario {user_id} registrado (allowed={auto_allow})")
        return user

    def register_chat_from_telegram(
        self,
        chat_id: int,
        title: str = None,
        chat_type: str = "private",
        auto_allow: bool = False
    ) -> Chat:
        """Registra un chat nuevo desde datos de Telegram"""
        chat = Chat(
            chat_id=chat_id,
            title=title,
            type=chat_type,
            is_allowed=auto_allow
        )
        self.chat_repo.save(chat)
        logger.info(f"Chat {chat_id} registrado (allowed={auto_allow})")
        return chat
