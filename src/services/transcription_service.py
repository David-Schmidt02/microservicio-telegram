import requests
from typing import Optional
from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TranscriptionService:
    """Servicio para transcribir audios usando la API externa"""

    def __init__(self):
        self.api_url = settings.TRANSCRIPTION_API_URL
        #self.api_key = settings.TRANSCRIPTION_API_KEY

    def transcribe_audio(self, audio_file_path: str) -> Optional[str]:
        """
        Transcribe un archivo de audio usando la API de transcripción

        Args:
            audio_file_path: Ruta local del archivo de audio

        Returns:
            Texto transcrito o None si falla
        """
        try:
            # Preparar headers con API key si existe
            headers = {}
            #if self.api_key:
            #    headers['Authorization'] = f'Bearer {self.api_key}'

            # Abrir el archivo de audio
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'audio': (audio_file_path, audio_file, 'audio/ogg')
                }

                # Enviar request a la API de transcripción
                logger.info(f"Enviando audio a transcribir: {audio_file_path}")
                response = requests.post(
                    self.api_url,
                    files=files,
                    headers=headers,
                    timeout=60
                )

                response.raise_for_status()
                data = response.json()

                # Extraer el texto transcrito
                # Ajusta este campo según la estructura de respuesta de tu API
                transcription = data.get('transcription') or data.get('text') or data.get('transcript')

                if transcription:
                    logger.info(f"Transcripción exitosa: {transcription[:100]}...")
                    return transcription
                else:
                    logger.error(f"No se encontró transcripción en la respuesta: {data}")
                    return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en la API de transcripción: {e}")
            return None
        except Exception as e:
            logger.error(f"Error al transcribir audio: {e}")
            return None

    def transcribe_audio_base64(self, audio_base64: str) -> Optional[str]:
        """
        Transcribe un audio en formato base64 (alternativa)

        Args:
            audio_base64: Audio codificado en base64

        Returns:
            Texto transcrito o None si falla
        """
        try:
            headers = {'Content-Type': 'application/json'}
            #if self.api_key:
            #    headers['Authorization'] = f'Bearer {self.api_key}'

            payload = {
                'audio': audio_base64
            }

            logger.info("Enviando audio en base64 a transcribir")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                timeout=60
            )

            response.raise_for_status()
            data = response.json()

            transcription = data.get('transcription') or data.get('text') or data.get('transcript')

            if transcription:
                logger.info(f"Transcripción exitosa: {transcription[:100]}...")
                return transcription
            else:
                logger.error(f"No se encontró transcripción en la respuesta: {data}")
                return None

        except Exception as e:
            logger.error(f"Error al transcribir audio base64: {e}")
            return None
