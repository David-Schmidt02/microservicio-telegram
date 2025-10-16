import asyncio
import requests
import os
from typing import Optional, List
from src.config.settings import settings
from src.utils.logger import setup_logger
from src.schemas import TelegramTextMessage, TelegramAudioMessage

logger = setup_logger(__name__)


class TelegramService:
    """Servicio para interactuar con la API de Telegram"""

    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0
        self.temp_audio_dir = "temp_audio"

        if not os.path.exists(self.temp_audio_dir):
            os.makedirs(self.temp_audio_dir)

    def get_updates(self, offset: Optional[int] = None) -> list:
        """Obtiene las actualizaciones del bot de Telegram."""

        url = f"{self.base_url}/getUpdates"
        params = {
            "timeout": 0, # le especifico un polling a telegram (ya lo hacemos con un sleep en el bot)
            "offset": offset
        }

        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            if data.get("ok"):
                return data.get("result", [])
            else:
                logger.error(f"Error en getUpdates: {data}")
                return []

        except requests.exceptions.RequestException as e:
            logger.error(f"Error al obtener actualizaciones de Telegram: {e}")
            return []

    def download_audio(self, file_id: str) -> str:
        """Descarga un archivo de audio de Telegram."""
        # Obtener información del archivo
        file_info_url = f"{self.base_url}/getFile"
        params = {"file_id": file_id}

        response = requests.get(file_info_url, params=params)
        response.raise_for_status()
        data = response.json()

        if not data.get("ok"):
            raise ValueError(f"Telegram API error: {data}")

        file_path = data["result"]["file_path"]

        # Descargar el archivo
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        audio_response = requests.get(download_url, timeout=30)
        audio_response.raise_for_status()

        # Guardar archivo localmente
        local_file_path = os.path.join(self.temp_audio_dir, f"{file_id}.ogg")
        with open(local_file_path, 'wb') as f:
            f.write(audio_response.content)

        logger.info(f"Audio descargado: {local_file_path}")
        return local_file_path

    def send_message(self, text: str, reply_to_message_id: Optional[int] = None) -> bool:
        """Envía un mensaje al chat configurado."""
        url = f"{self.base_url}/sendMessage"
        payload: dict[str, str | int] = { # Diccionario con claves str y valores str o int
            "chat_id": self.chat_id,
            "text": text
        }
        logger.info("PASO 4 - Enviar mensaje al chat")
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            response = requests.post(url, json=payload, timeout=1)
            response.raise_for_status()
            return response.json().get("ok", False)

        except Exception as e:
            logger.error(f"Error al enviar mensaje: {e}")
            return False

    async def _process_update(self, update, audio_callback, text_callback):
        """Procesa un update individual. Parsea el mensaje y llama al callback correspondiente."""
        message = update.get("message", {})
        logger.info("PASO 2 - process_update")
        try:
            # Procesar mensaje de audio/voz
            if "voice" in message or "audio" in message:
                msg = TelegramAudioMessage.from_telegram_update(update)
                logger.info(f"Audio de {msg.user.get_display_name()}")
                await audio_callback(msg)

            # Procesar mensaje de texto
            elif "text" in message:
                msg = TelegramTextMessage.from_telegram_update(update)
                logger.info(f"Texto de {msg.user.get_display_name()}: {msg.text}...")
                await text_callback(msg)

        except Exception as e:
            logger.error(f"Error al procesar mensaje (update_id: {update.get('update_id')}): {e}")

    async def start_polling(self, audio_callback, text_callback):
        """Inicia el polling. Procesa mensajes en orden cronológico."""
        logger.info("Iniciando polling de Telegram...")

        while True:
            try:
                # Obtener actualizaciones
                offset = self.last_update_id + 1 if self.last_update_id > 0 else None
                updates = self.get_updates(offset)
                logger.info("PASO 1 - get_updates")
                if updates:
                    # Actualizar el último update_id
                    self.last_update_id = max(update["update_id"] for update in updates)

                    # Procesar cada mensaje en orden cronológico
                    for update in updates:
                        await self._process_update(update, audio_callback, text_callback)

                # Esperar el intervalo configurado antes del siguiente poll
                await asyncio.sleep(settings.POLLING_INTERVAL)

            except Exception as e:
                logger.error(f"Error en el polling: {e}")
                await asyncio.sleep(settings.POLLING_INTERVAL)

    def cleanup_audio_file(self, file_path: str):
        """Elimina un archivo de audio temporal."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.error(f"Error al eliminar archivo {file_path}: {e}")
