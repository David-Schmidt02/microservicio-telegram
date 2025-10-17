import aiohttp
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class QueryService:

    def __init__(self):
        self.api_url = settings.QUERY_SYSTEM_URL
        self._session: Optional[aiohttp.ClientSession] = None
        #self.api_key = settings.QUERY_SYSTEM_API_KEY

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea la sesión de aiohttp."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Cierra la sesión de aiohttp."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def send_query(self, question: str, session_id: str = "telegram-bot-session", retries: int = 1) -> Dict[str, Any]:
        """Envía una query al sistema destino y retorna la respuesta."""
        headers = {'Content-Type': 'application/json'}
        #if self.api_key:
        #    headers['Authorization'] = f'Bearer {self.api_key}'

        payload = {
            'question': question,
            'session_id': session_id
        }

        logger.info(f"Enviando query al sistema: {question}...")

        session = await self._get_session()

        async with session.post(
            self.api_url,
            json=payload,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            response.raise_for_status()
            result = await response.json()

            # Validar que la respuesta sea exitosa
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                raise ValueError(f"Query failed: {error_msg}")

            logger.info(f"Query procesada exitosamente. Answer: {result.get('answer')}")
            return result