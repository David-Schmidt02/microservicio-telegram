import asyncio
import aiohttp
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
        self._session: Optional[aiohttp.ClientSession] = None

        if not os.path.exists(self.temp_audio_dir):
            os.makedirs(self.temp_audio_dir)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea la sesión de aiohttp."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Cierra la sesión de aiohttp."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_updates(self, offset: Optional[int] = None) -> list:
        """Obtiene las actualizaciones del bot de Telegram."""
        url = f"{self.base_url}/getUpdates"
        params: dict[str, int] = {
            "timeout": 0,  # le especifico un polling a telegram (ya lo hacemos con un sleep en el bot)
        }

        # Solo agregar offset si no es None (aiohttp no acepta None como valor)
        if offset is not None:
            params["offset"] = offset

        try:
            session = await self._get_session()
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
                response.raise_for_status()
                data = await response.json()

                if data.get("ok"):
                    return data.get("result", [])
                else:
                    logger.error(f"Error en getUpdates: {data}")
                    return []

        except aiohttp.ClientError as e:
            logger.error(f"Error al obtener actualizaciones de Telegram: {e}")
            return []
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout al obtener actualizaciones de Telegram: {e}")
            return []

    async def download_audio(self, file_id: str, retries: int = 0) -> str:
        """Descarga un archivo de audio de Telegram."""
        # Obtener información del archivo
        file_info_url = f"{self.base_url}/getFile"
        params = {"file_id": file_id}

        session = await self._get_session()

        async with session.get(file_info_url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

            if not data.get("ok"):
                raise ValueError(f"Telegram API error: {data}")

            file_path = data["result"]["file_path"]

        # Descargar el archivo
        download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
        async with session.get(download_url, timeout=aiohttp.ClientTimeout(total=30)) as audio_response:
            audio_response.raise_for_status()
            audio_content = await audio_response.read()

        # Guardar archivo localmente
        local_file_path = os.path.join(self.temp_audio_dir, f"{file_id}.ogg")
        with open(local_file_path, 'wb') as f:
            f.write(audio_content)

        logger.info(f"Audio descargado: {local_file_path}")
        return local_file_path

    async def send_message(self, text: str, reply_to_message_id: Optional[int] = None, retries: int = 0) -> bool:
        """Envía un mensaje al chat configurado."""
        url = f"{self.base_url}/sendMessage"
        payload: dict[str, str | int] = {  # Diccionario con claves str y valores str o int
            "chat_id": self.chat_id,
            "text": text
        }
        logger.info("PASO 4 - Enviar mensaje al chat")
        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            session = await self._get_session()
            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("ok", False)

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
                updates = await self.get_updates(offset)
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
