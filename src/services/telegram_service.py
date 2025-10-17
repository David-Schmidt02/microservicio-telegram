import asyncio
import aiohttp
import os
from typing import Optional, List
from src.config.settings import settings
from src.utils.logger import setup_logger
from src.schemas import TelegramTextMessage, TelegramAudioMessage
from src.services.authorization_service import AuthorizationService

logger = setup_logger(__name__)


class TelegramService:
    """Servicio para interactuar con la API de Telegram"""

    def __init__(self, authorization_service: AuthorizationService = None):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0
        self.temp_audio_dir = "temp_audio"
        self._session: Optional[aiohttp.ClientSession] = None
        self.auth_service = authorization_service or AuthorizationService()

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

    def _split_by_incidents(self, text: str) -> List[str]:
        """Divide el mensaje por incidentes usando --- como separador."""
        parts = text.split('---')
        # Filtrar partes vacías
        return [part.strip() for part in parts if part.strip()]

    async def _send_message_parts(self, parts: List[str], reply_to_message_id: Optional[int] = None) -> bool:
        """Envía múltiples partes de un mensaje al chat."""
        url = f"{self.base_url}/sendMessage"
        all_success = True

        for i, part in enumerate(parts):
            payload = {
                "chat_id": self.chat_id,
                "text": part
            }

            # Solo el primer mensaje responde al mensaje original
            if reply_to_message_id and i == 0:
                payload["reply_to_message_id"] = reply_to_message_id

            try:
                session = await self._get_session()
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if not data.get("ok", False):
                        logger.error(f"Error al enviar parte {i+1}/{len(parts)}")
                        all_success = False

                # Pausa entre mensajes
                if i < len(parts) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error al enviar mensaje parte {i+1}: {e}")
                all_success = False

        return all_success

    async def send_message(self, text: str, reply_to_message_id: Optional[int] = None, retries: int = 0) -> bool:
        """Envía un mensaje al chat configurado. Si tiene incidentes separados por ---, los envía por separado."""
        logger.info("PASO 4 - Enviar mensaje al chat")

        # Dividir por incidentes
        parts = self._split_by_incidents(text)

        # Enviar las partes
        return await self._send_message_parts(parts, reply_to_message_id)

    async def _process_update(self, update, audio_callback, text_callback):
        """Procesa un update individual. Parsea el mensaje y llama al callback correspondiente."""
        message = update.get("message", {})
        logger.info("PASO 2 - process_update")
        try:
            # Procesar mensaje de audio/voz
            if "voice" in message or "audio" in message:
                msg = TelegramAudioMessage.from_telegram_update(update)
                logger.info(f"Audio de {msg.user.get_display_name()}")

                # Validar whitelist
                if not self.auth_service.is_message_allowed(msg.user.user_id, msg.chat.chat_id):
                    await self.send_message(
                        "⛔ No estás autorizado para usar este bot.",
                        reply_to_message_id=msg.message_id
                    )
                    return

                await audio_callback(msg)

            # Procesar mensaje de texto
            elif "text" in message:
                msg = TelegramTextMessage.from_telegram_update(update)
                logger.info(f"Texto de {msg.user.get_display_name()}: {msg.text}...")

                # Validar whitelist
                if not self.auth_service.is_message_allowed(msg.user.user_id, msg.chat.chat_id):
                    await self.send_message(
                        "⛔ No estás autorizado para usar este bot.",
                        reply_to_message_id=msg.message_id
                    )
                    return

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
