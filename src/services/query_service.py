import requests
from typing import Dict, Any
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryService:

    def __init__(self):
        self.api_url = settings.QUERY_SYSTEM_URL
        #self.api_key = settings.QUERY_SYSTEM_API_KEY

    def send_query(self, question: str, session_id: str = "telegram-bot-session") -> Dict[str, Any]:
        """Envía una query al sistema destino y retorna la respuesta."""
        headers = {'Content-Type': 'application/json'}
        #if self.api_key:
        #    headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'question': question,
            'session_id': session_id
        }

        logger.info(f"Enviando query al sistema: {question}...")

        response = requests.post(
            self.api_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()

        result = response.json()

        # Validar que la respuesta sea exitosa
        if not result.get('success'):
            error_msg = result.get('error', 'Unknown error')
            raise ValueError(f"Query failed: {error_msg}")

        logger.info(f"Query procesada exitosamente. Answer: {result.get('answer')}")
        return result