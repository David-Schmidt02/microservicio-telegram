import aiohttp
from typing import Optional
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptionService:
    """Servicio para transcribir audios usando la API externa"""

    def __init__(self):
        self.api_url = settings.TRANSCRIPTION_API_URL
        self._session: Optional[aiohttp.ClientSession] = None
        #self.api_key = settings.TRANSCRIPTION_API_KEY

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea la sesión de aiohttp."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Cierra la sesión de aiohttp."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def transcribe_audio(self, audio_file_path: str, retries: int = 0) -> str:
        """Transcribe un archivo de audio usando la API externa."""
        headers = {}
        #if self.api_key:
        #    headers['Authorization'] = f'Bearer {self.api_key}'

        logger.info(f"Enviando audio a transcribir: {audio_file_path}")

        session = await self._get_session()

        with open(audio_file_path, 'rb') as audio_file:
            data = aiohttp.FormData()
            data.add_field('audio', audio_file, filename=audio_file_path, content_type='audio/ogg')

            async with session.post(
                self.api_url,
                data=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response.raise_for_status()
                result = await response.json()

                transcription = result.get('transcription')

                if not transcription:
                    raise ValueError(f"No 'transcription' field in API response: {result}")

                logger.info(f"Transcripción exitosa: {transcription[:100]}...")
                return transcription
