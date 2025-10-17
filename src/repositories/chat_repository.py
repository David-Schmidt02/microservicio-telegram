"""Repositorio de chats con implementación YAML"""
import yaml
import os
from typing import Optional, List
from src.repositories.base_repository import BaseRepository
from src.models.chat import Chat
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ChatRepository(BaseRepository[Chat]):
    """Repositorio de chats usando archivo YAML como persistencia"""

    def __init__(self, file_path: str = "data/chats.yaml"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Crea el archivo y directorio si no existen"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                yaml.dump({"chats": []}, f)
            logger.info(f"Archivo de chats creado: {self.file_path}")

    def _load_data(self) -> dict:
        """Carga los datos del archivo YAML"""
        try:
            with open(self.file_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                return data
        except Exception as e:
            logger.error(f"Error al cargar chats: {e}")
            return {"chats": []}

    def _save_data(self, data: dict):
        """Guarda los datos en el archivo YAML"""
        try:
            with open(self.file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.debug(f"Chats guardados en {self.file_path}")
        except Exception as e:
            logger.error(f"Error al guardar chats: {e}")
            raise

    def get_by_id(self, chat_id: int) -> Optional[Chat]:
        """Obtiene un chat por su ID"""
        data = self._load_data()
        chats_data = data.get("chats", [])

        for chat_data in chats_data:
            if chat_data.get("chat_id") == chat_id:
                return Chat.from_dict(chat_data)

        return None

    def get_all(self) -> List[Chat]:
        """Obtiene todos los chats"""
        data = self._load_data()
        chats_data = data.get("chats", [])
        return [Chat.from_dict(chat_data) for chat_data in chats_data]

    def save(self, chat: Chat) -> Chat:
        """Guarda o actualiza un chat"""
        data = self._load_data()
        chats_data = data.get("chats", [])

        # Buscar si ya existe
        chat_index = None
        for i, chat_data in enumerate(chats_data):
            if chat_data.get("chat_id") == chat.chat_id:
                chat_index = i
                break

        chat_dict = chat.to_dict()

        if chat_index is not None:
            # Actualizar existente
            chats_data[chat_index] = chat_dict
            logger.info(f"Chat {chat.chat_id} actualizado")
        else:
            # Crear nuevo
            chats_data.append(chat_dict)
            logger.info(f"Chat {chat.chat_id} creado")

        data["chats"] = chats_data
        self._save_data(data)

        return chat

    def delete(self, chat_id: int) -> bool:
        """Elimina un chat por su ID"""
        data = self._load_data()
        chats_data = data.get("chats", [])

        original_length = len(chats_data)
        chats_data = [c for c in chats_data if c.get("chat_id") != chat_id]

        if len(chats_data) < original_length:
            data["chats"] = chats_data
            self._save_data(data)
            logger.info(f"Chat {chat_id} eliminado")
            return True

        return False

    def exists(self, chat_id: int) -> bool:
        """Verifica si existe un chat con el ID dado"""
        return self.get_by_id(chat_id) is not None

    def get_allowed_chats(self) -> List[Chat]:
        """Obtiene solo los chats permitidos (whitelist)"""
        all_chats = self.get_all()
        return [chat for chat in all_chats if chat.is_allowed]
