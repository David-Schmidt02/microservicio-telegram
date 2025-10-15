import asyncio
import requests
import os
from typing import Optional, List, Dict, Any
from src.config.settings import settings
from src.utils.logger import setup_logger

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

    def get_updates(self, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Obtiene las actualizaciones del bot de Telegram

        Args:
            offset: ID del último update procesado + 1

        Returns:
            Lista de actualizaciones
        """
        url = f"{self.base_url}/getUpdates"
        params = {
            "timeout": 0,
            "offset": offset
        }

        try:
            response = requests.get(url, params=params, timeout=10)
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

    def download_audio(self, file_id: str) -> Optional[str]:
        """
        Descarga un archivo de audio de Telegram

        Args:
            file_id: ID del archivo en Telegram

        Returns:
            Ruta local del archivo descargado o None si falla
        """
        try:
            # Obtener información del archivo
            file_info_url = f"{self.base_url}/getFile"
            params = {"file_id": file_id}

            response = requests.get(file_info_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if not data.get("ok"):
                logger.error(f"Error al obtener info del archivo: {data}")
                return None

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

        except Exception as e:
            logger.error(f"Error al descargar audio: {e}")
            return None

    def send_message(self, text: str, reply_to_message_id: Optional[int] = None) -> bool:
        """
        Envía un mensaje al chat configurado

        Args:
            text: Texto del mensaje
            reply_to_message_id: ID del mensaje al que responder

        Returns:
            True si el mensaje se envió correctamente
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }

        if reply_to_message_id:
            payload["reply_to_message_id"] = reply_to_message_id

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json().get("ok", False)

        except Exception as e:
            logger.error(f"Error al enviar mensaje: {e}")
            return False

    def extract_audio_messages(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extrae mensajes que contienen audio de las actualizaciones

        Args:
            updates: Lista de actualizaciones de Telegram

        Returns:
            Lista de mensajes con audio
        """
        audio_messages = []

        for update in updates:
            message = update.get("message", {})

            # Verificar si el mensaje tiene audio o voice
            if "voice" in message or "audio" in message:
                audio_info = message.get("voice") or message.get("audio")
                from_user = message.get("from", {})
                chat_info = message.get("chat", {})

                # Construir nombre completo del usuario
                full_name = from_user.get("first_name", "")
                if from_user.get("last_name"):
                    full_name += f" {from_user.get('last_name')}"

                audio_messages.append({
                    "update_id": update["update_id"],
                    "message_id": message["message_id"],
                    "file_id": audio_info["file_id"],
                    "duration": audio_info.get("duration"),

                    # Información del chat/grupo
                    "chat_id": chat_info.get("id"),
                    "chat_type": chat_info.get("type"),  # "private", "group", "supergroup"
                    "chat_title": chat_info.get("title"),  # Nombre del grupo

                    # Información del usuario
                    "user_id": from_user.get("id"),
                    "username": from_user.get("username"),  # @username
                    "user_first_name": from_user.get("first_name"),
                    "user_last_name": from_user.get("last_name"),
                    "user_full_name": full_name,
                    "user_language_code": from_user.get("language_code"),
                    "is_bot": from_user.get("is_bot", False),

                    # Timestamp
                    "date": message.get("date")
                })

                username_display = audio_messages[-1]['username'] or audio_messages[-1]['user_full_name']
                logger.info(f"Mensaje de audio detectado de {username_display} (ID: {audio_messages[-1]['user_id']})")

        return audio_messages

    def extract_text_messages(self, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extrae mensajes de texto de las actualizaciones

        Args:
            updates: Lista de actualizaciones de Telegram

        Returns:
            Lista de mensajes de texto
        """
        text_messages = []

        for update in updates:
            message = update.get("message", {})

            # Verificar si el mensaje tiene texto (y no es audio/voice)
            if "text" in message and "voice" not in message and "audio" not in message:
                from_user = message.get("from", {})
                chat_info = message.get("chat", {})

                # Construir nombre completo del usuario
                full_name = from_user.get("first_name", "")
                if from_user.get("last_name"):
                    full_name += f" {from_user.get('last_name')}"

                text_messages.append({
                    "update_id": update["update_id"],
                    "message_id": message["message_id"],
                    "text": message["text"],

                    # Información del chat/grupo
                    "chat_id": chat_info.get("id"),
                    "chat_type": chat_info.get("type"),  # "private", "group", "supergroup"
                    "chat_title": chat_info.get("title"),  # Nombre del grupo

                    # Información del usuario
                    "user_id": from_user.get("id"),
                    "username": from_user.get("username"),  # @username
                    "user_first_name": from_user.get("first_name"),
                    "user_last_name": from_user.get("last_name"),
                    "user_full_name": full_name,
                    "user_language_code": from_user.get("language_code"),
                    "is_bot": from_user.get("is_bot", False),

                    # Timestamp
                    "date": message.get("date")
                })

                username_display = text_messages[-1]['username'] or text_messages[-1]['user_full_name']
                logger.info(f"Mensaje de texto detectado de {username_display} (ID: {text_messages[-1]['user_id']}): {message['text'][:50]}...")

        return text_messages

    async def start_polling(self, audio_callback, text_callback):
        """
        Inicia el polling para obtener actualizaciones cada 2-3 segundos

        Args:
            audio_callback: Función callback a ejecutar cuando se detecta un mensaje de audio
            text_callback: Función callback a ejecutar cuando se detecta un mensaje de texto
        """
        logger.info("Iniciando polling de Telegram...")

        while True:
            try:
                # Obtener actualizaciones
                offset = self.last_update_id + 1 if self.last_update_id > 0 else None
                updates = self.get_updates(offset)

                if updates:
                    # Actualizar el último update_id
                    self.last_update_id = max(update["update_id"] for update in updates)

                    # Extraer mensajes con audio
                    audio_messages = self.extract_audio_messages(updates)

                    # Procesar cada mensaje de audio
                    for audio_msg in audio_messages:
                        await audio_callback(audio_msg)

                    # Extraer mensajes de texto
                    text_messages = self.extract_text_messages(updates)

                    # Procesar cada mensaje de texto
                    for text_msg in text_messages:
                        await text_callback(text_msg)

                # Esperar el intervalo configurado antes del siguiente poll
                await asyncio.sleep(settings.POLLING_INTERVAL)

            except Exception as e:
                logger.error(f"Error en el polling: {e}")
                await asyncio.sleep(settings.POLLING_INTERVAL)

    def cleanup_audio_file(self, file_path: str):
        """
        Elimina un archivo de audio temporal

        Args:
            file_path: Ruta del archivo a eliminar
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Archivo eliminado: {file_path}")
        except Exception as e:
            logger.error(f"Error al eliminar archivo {file_path}: {e}")
