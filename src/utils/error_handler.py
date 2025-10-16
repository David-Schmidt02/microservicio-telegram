"""
Middleware para manejo centralizado de errores en callbacks de Telegram.
Similar a los error handlers de Express.js
"""
import aiohttp
from functools import wraps
from typing import Callable
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def handle_telegram_errors(cleanup_audio: bool = False):
    """
    Decorador que actúa como middleware para manejar errores en callbacks de Telegram.

    Args:
        cleanup_audio: Si True, espera que la función retorne (result, audio_path)
                       para hacer cleanup del archivo temporal

    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(self, message, *args, **kwargs):
            audio_file_path = None

            try:
                # Ejecutar la función original
                result = await func(self, message, *args, **kwargs)

                # Si retorna tupla con audio_path, extraerlo
                if cleanup_audio and isinstance(result, tuple):
                    _, audio_file_path = result

                return result

            except FileNotFoundError as e:
                logger.error(f"Archivo no encontrado: {e}")
                await self.telegram_service.send_message(
                    "❌ Error: Archivo no encontrado",
                    reply_to_message_id=message.message_id
                )

            except aiohttp.ClientResponseError as e:
                logger.error(f"Error HTTP de API: {e}")
                await self.telegram_service.send_message(
                    f"❌ Error de conexión con API (HTTP {e.status})",
                    reply_to_message_id=message.message_id
                )

            except aiohttp.ClientError as e:
                logger.error(f"Error de conexión con API: {e}")
                await self.telegram_service.send_message(
                    "⏱️ Error: La API tardó demasiado en responder o falló la conexión",
                    reply_to_message_id=message.message_id
                )

            except ValueError as e:
                logger.error(f"Error de validación: {e}")
                await self.telegram_service.send_message(
                    f"⚠️ Error al procesar: {str(e)}",
                    reply_to_message_id=message.message_id
                )

            except Exception as e:
                logger.error(f"Error inesperado en {func.__name__}: {e}", exc_info=True)
                await self.telegram_service.send_message(
                    f"💥 Error inesperado: {str(e)}",
                    reply_to_message_id=message.message_id
                )

            finally:
                # Cleanup de archivos temporales si es necesario
                if cleanup_audio and audio_file_path:
                    try:
                        self.telegram_service.cleanup_audio_file(audio_file_path)
                    except Exception as cleanup_error:
                        logger.error(f"Error en cleanup: {cleanup_error}")

        return wrapper
    return decorator
