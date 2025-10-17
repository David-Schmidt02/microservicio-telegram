"""Repositorio de usuarios con implementación YAML"""
import yaml
import os
from typing import Optional, List
from src.repositories.base_repository import BaseRepository
from src.models.user import User
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repositorio de usuarios usando archivo YAML como persistencia"""

    def __init__(self, file_path: str = "data/users.yaml"):
        self.file_path = file_path
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Crea el archivo y directorio si no existen"""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                yaml.dump({"users": []}, f)
            logger.info(f"Archivo de usuarios creado: {self.file_path}")

    def _load_data(self) -> dict:
        """Carga los datos del archivo YAML"""
        try:
            with open(self.file_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                return data
        except Exception as e:
            logger.error(f"Error al cargar usuarios: {e}")
            return {"users": []}

    def _save_data(self, data: dict):
        """Guarda los datos en el archivo YAML"""
        try:
            with open(self.file_path, 'w') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
            logger.debug(f"Usuarios guardados en {self.file_path}")
        except Exception as e:
            logger.error(f"Error al guardar usuarios: {e}")
            raise

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Obtiene un usuario por su ID"""
        data = self._load_data()
        users_data = data.get("users", [])

        for user_data in users_data:
            if user_data.get("user_id") == user_id:
                return User.from_dict(user_data)

        return None

    def get_all(self) -> List[User]:
        """Obtiene todos los usuarios"""
        data = self._load_data()
        users_data = data.get("users", [])
        return [User.from_dict(user_data) for user_data in users_data]

    def save(self, user: User) -> User:
        """Guarda o actualiza un usuario"""
        data = self._load_data()
        users_data = data.get("users", [])

        # Buscar si ya existe
        user_index = None
        for i, user_data in enumerate(users_data):
            if user_data.get("user_id") == user.user_id:
                user_index = i
                break

        user_dict = user.to_dict()

        if user_index is not None:
            # Actualizar existente
            users_data[user_index] = user_dict
            logger.info(f"Usuario {user.user_id} actualizado")
        else:
            # Crear nuevo
            users_data.append(user_dict)
            logger.info(f"Usuario {user.user_id} creado")

        data["users"] = users_data
        self._save_data(data)

        return user

    def delete(self, user_id: int) -> bool:
        """Elimina un usuario por su ID"""
        data = self._load_data()
        users_data = data.get("users", [])

        original_length = len(users_data)
        users_data = [u for u in users_data if u.get("user_id") != user_id]

        if len(users_data) < original_length:
            data["users"] = users_data
            self._save_data(data)
            logger.info(f"Usuario {user_id} eliminado")
            return True

        return False

    def exists(self, user_id: int) -> bool:
        """Verifica si existe un usuario con el ID dado"""
        return self.get_by_id(user_id) is not None

    def get_allowed_users(self) -> List[User]:
        """Obtiene solo los usuarios permitidos (whitelist)"""
        all_users = self.get_all()
        return [user for user in all_users if user.is_allowed]
