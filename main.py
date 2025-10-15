import asyncio
from src.config.settings import settings
from src.services.telegram_service import TelegramService
from src.services.transcription_service import TranscriptionService
from src.services.query_service import QueryService
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class TelegramAudioBot:
    """Microservicio principal del bot de Telegram para procesar audios y mensajes de texto"""

    def __init__(self):
        self.telegram_service = TelegramService()
        self.transcription_service = TranscriptionService()
        self.query_service = QueryService()

    async def process_audio_message(self, audio_message: dict):
        """
        Procesa un mensaje de audio completo:
        1. Descarga el audio
        2. Lo transcribe
        3. Envía la transcripción al sistema de queries

        Args:
            audio_message: Diccionario con información del mensaje de audio
        """
        try:
            user_display = audio_message['username'] or audio_message['user_full_name']
            logger.info(f"Procesando mensaje de audio de {user_display} (ID: {audio_message['user_id']})")

            # Paso 1: Descargar el audio
            audio_file_path = self.telegram_service.download_audio(audio_message['file_id'])

            if not audio_file_path:
                logger.error("No se pudo descargar el audio")
                self.telegram_service.send_message(
                    "❌ Error al descargar el audio",
                    reply_to_message_id=audio_message['message_id']
                )
                return

            # Paso 2: Transcribir el audio
            logger.info("Transcribiendo audio...")
            transcription = self.transcription_service.transcribe_audio(audio_file_path)

            if not transcription:
                logger.error("No se pudo transcribir el audio")
                self.telegram_service.send_message(
                    "❌ Error al transcribir el audio",
                    reply_to_message_id=audio_message['message_id']
                )
                self.telegram_service.cleanup_audio_file(audio_file_path)
                return

            logger.info(f"Transcripción obtenida: {transcription}")

            # Paso 3: Enviar la query al sistema
            # Usar el chat_id (ID del grupo) como session_id para mantener contexto por grupo
            session_id = f"telegram-group-{audio_message['chat_id']}"

            # Información disponible del usuario (no se envía al sistema de queries):
            # - user_id: {audio_message['user_id']}
            # - username: {audio_message['username']}
            # - user_full_name: {audio_message['user_full_name']}
            # - chat_type: {audio_message['chat_type']}
            # - chat_title: {audio_message['chat_title']}

            logger.info(f"Enviando query al sistema (Usuario: {audio_message['username'] or audio_message['user_full_name']})...")
            result = self.query_service.send_query(transcription, session_id)

            if result and result.get('success'):
                answer = result.get('answer', 'No se obtuvo respuesta')
                logger.info("Query procesada exitosamente")
                self.telegram_service.send_message(
                    f"🎤 Audio: {transcription}\n\n💬 Respuesta: {answer}",
                    reply_to_message_id=audio_message['message_id']
                )
            else:
                logger.error("Error al procesar query en el sistema")
                error_msg = result.get('error', 'Error desconocido') if result else 'Sin respuesta del servidor'
                self.telegram_service.send_message(
                    f"⚠️ Error al procesar la consulta\n\n📝 Transcripción: {transcription}\n❌ Error: {error_msg}",
                    reply_to_message_id=audio_message['message_id']
                )

            # Limpiar el archivo temporal
            self.telegram_service.cleanup_audio_file(audio_file_path)

        except Exception as e:
            logger.error(f"Error al procesar mensaje de audio: {e}")
            self.telegram_service.send_message(
                f"❌ Error inesperado al procesar el audio: {str(e)}",
                reply_to_message_id=audio_message.get('message_id')
            )

    async def process_text_message(self, text_message: dict):
        """
        Procesa un mensaje de texto:
        1. Toma el texto directamente
        2. Lo envía al sistema de queries

        Args:
            text_message: Diccionario con información del mensaje de texto
        """
        try:
            user_display = text_message['username'] or text_message['user_full_name']
            logger.info(f"Procesando mensaje de texto de {user_display} (ID: {text_message['user_id']})")

            text = text_message['text']
            logger.info(f"Texto recibido: {text}")

            # Enviar la query al sistema
            # Usar el chat_id (ID del grupo) como session_id para mantener contexto por grupo
            session_id = f"telegram-group-{text_message['chat_id']}"

            # Información disponible del usuario (no se envía al sistema de queries):
            # - user_id: {text_message['user_id']}
            # - username: {text_message['username']}
            # - user_full_name: {text_message['user_full_name']}
            # - chat_type: {text_message['chat_type']}
            # - chat_title: {text_message['chat_title']}

            logger.info(f"Enviando query al sistema (Usuario: {user_display})...")
            result = self.query_service.send_query(text, session_id)

            if result and result.get('success'):
                answer = result.get('answer', 'No se obtuvo respuesta')
                logger.info("Query procesada exitosamente")
                self.telegram_service.send_message(
                    f"💬 Respuesta: {answer}",
                    reply_to_message_id=text_message['message_id']
                )
            else:
                logger.error("Error al procesar query en el sistema")
                error_msg = result.get('error', 'Error desconocido') if result else 'Sin respuesta del servidor'
                self.telegram_service.send_message(
                    f"⚠️ Error al procesar la consulta\n\n❌ Error: {error_msg}",
                    reply_to_message_id=text_message['message_id']
                )

        except Exception as e:
            logger.error(f"Error al procesar mensaje de texto: {e}")
            self.telegram_service.send_message(
                f"❌ Error inesperado al procesar el mensaje: {str(e)}",
                reply_to_message_id=text_message.get('message_id')
            )

    async def start(self):
        """Inicia el microservicio"""
        try:
            logger.info("=" * 60)
            logger.info("Iniciando Microservicio de Telegram Bot")
            logger.info("=" * 60)

            # Validar configuración
            settings.validate()
            logger.info("✓ Configuración validada correctamente")

            # Información del bot
            logger.info(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
            logger.info(f"Intervalo de polling: {settings.POLLING_INTERVAL} segundos")
            logger.info(f"API de transcripción: {settings.TRANSCRIPTION_API_URL}")
            logger.info(f"Sistema de queries: {settings.QUERY_SYSTEM_URL}")

            # Iniciar polling
            logger.info("\n🚀 Bot iniciado. Esperando mensajes de audio y texto...\n")
            await self.telegram_service.start_polling(
                self.process_audio_message,
                self.process_text_message
            )

        except ValueError as e:
            logger.error(f"Error de configuración: {e}")
            logger.error("Por favor, configura las variables de entorno en el archivo .env")
        except KeyboardInterrupt:
            logger.info("\n\n⏹️  Bot detenido por el usuario")
        except Exception as e:
            logger.error(f"Error fatal: {e}")


def main():
    """Función principal"""
    bot = TelegramAudioBot()
    asyncio.run(bot.start())


if __name__ == "__main__":
    main()
