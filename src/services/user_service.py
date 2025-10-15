import requests
from typing import Optional, Dict, Any
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class UserService:
    """Servicio para gestionar usuarios, validación y obtención de su id"""

    def __init__(self):
        self.api_url = settings.USER_SYSTEM_URL
        #self.api_key = settings.USER_SYSTEM_API_KEY

    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información del usuario desde el sistema destino

        Args:
            user_id: ID del usuario

        Returns:
            Diccionario con la información del usuario o None si falla
        """
        try:
            # Preparar headers
            headers = {'Content-Type': 'application/json'}
            #if self.api_key:
            #    headers['Authorization'] = f'Bearer {self.api_key}'

            # Enviar request
            logger.info(f"Obteniendo información del usuario: {user_id}...")
            response = requests.get(
                f"{self.api_url}/{user_id}",
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Información del usuario obtenida exitosamente: {result.get('name', 'N/A')}")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener información del usuario: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al obtener información del usuario: {e}")
            return None