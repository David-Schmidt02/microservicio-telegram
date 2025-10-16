import requests
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptionService:
    """Servicio para transcribir audios usando la API externa"""

    def __init__(self):
        self.api_url = settings.TRANSCRIPTION_API_URL
        #self.api_key = settings.TRANSCRIPTION_API_KEY

    def transcribe_audio(self, audio_file_path: str) -> str:
        """Transcribe un archivo de audio usando la API externa."""
        headers = {}
        #if self.api_key:
        #    headers['Authorization'] = f'Bearer {self.api_key}'

        logger.info(f"Enviando audio a transcribir: {audio_file_path}")

        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'audio': (audio_file_path, audio_file, 'audio/ogg')
            }

            response = requests.post(
                self.api_url,
                files=files,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            data = response.json()
            transcription = data.get('transcription')

            if not transcription:
                raise ValueError(f"No 'transcription' field in API response: {data}")

            logger.info(f"Transcripción exitosa: {transcription[:100]}...")
            return transcription
