import requests
from typing import Optional, Dict, Any
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryService:

    def __init__(self):
        self.api_url = settings.QUERY_SYSTEM_URL
        #self.api_key = settings.QUERY_SYSTEM_API_KEY

    def send_query(self, query_text: str, session_id: str = "telegram-bot-session") -> Optional[Dict[str, Any]]:
        """
        Envía una query al sistema destino y retorna la respuesta

        Args:
            query_text: Texto de la query (transcripción del audio)
            session_id: ID de sesión para mantener contexto

        Returns:
            Diccionario con la respuesta del sistema o None si falla
        """
        try:
            # Preparar headers
            headers = {'Content-Type': 'application/json'}
            #if self.api_key:
            #    headers['Authorization'] = f'Bearer {self.api_key}'

            # Preparar payload
            payload = {
                'question': query_text,
                'session_id': session_id
            }

            # Enviar request
            logger.info(f"Enviando query al sistema: {query_text[:100]}...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Query procesada exitosamente. Answer: {result.get('answer', 'N/A')[:100]}...")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al enviar query: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al enviar query: {e}")
            return None

    def send_query_with_response(self, query_text: str, metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Envía una query y retorna la respuesta completa del sistema

        Args:
            query_text: Texto de la query (transcripción del audio)
            metadata: Metadatos adicionales

        Returns:
            Respuesta del sistema o None si falla
        """
        try:
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'

            payload = {
                'question': query_text,
                'source': 'telegram_bot'
            }

            if metadata:
                payload['metadata'] = metadata

            logger.info(f"Enviando query con respuesta: {query_text[:100]}...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()
            result = response.json()

            logger.info("Query procesada exitosamente")
            return result

        except Exception as e:
            logger.error(f"Error al enviar query con respuesta: {e}")
            return None
