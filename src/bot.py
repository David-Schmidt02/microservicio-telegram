from src.config.settings import settings
from src.services.telegram_service import TelegramService
from src.services.transcription_service import TranscriptionService
from src.services.query_service import QueryService
from src.schemas import TelegramTextMessage, TelegramAudioMessage
from src.utils.logger import setup_logger
from src.utils.error_handler import handle_telegram_errors

logger = setup_logger(__name__)

class TelegramAudioBot:
    """Application service que orquesta los servicios de Telegram, transcripción y queries."""

    def __init__(self):
        self.telegram_service = TelegramService()
        self.transcription_service = TranscriptionService()
        self.query_service = QueryService()


    @handle_telegram_errors()
    async def process_text_message(self, text_message: TelegramTextMessage):
        """Procesa un mensaje de texto y lo envía al sistema de queries."""
        user_display = text_message.user.get_display_name()
        logger.info(f"Procesando mensaje de texto de {user_display}")
        logger.info(f"Texto: {text_message.text}")

        # Usar el chat_id (ID del grupo) como session_id para mantener contexto por grupo
        session_id = f"telegram-group-{text_message.chat.chat_id}"
        logger.info("PASO 3 - process_text_message")
        # Paso 1: Enviar query con la session_id del chat
        result = await self.query_service.send_query(text_message.text, session_id)
        
        # Paso 2: Obtener la respuesta
        answer = result.get('answer', 'No se obtuvo respuesta')

        # Paso 3: Enviar la respuesta al chat
        await self.telegram_service.send_message(
            f"{answer}",
            reply_to_message_id=text_message.message_id
        )


    @handle_telegram_errors(cleanup_audio=True)
    async def process_audio_message(self, audio_message: TelegramAudioMessage):
        """Descarga el audio, transcribe y envía la query al sistema."""
        user_display = audio_message.user.get_display_name()
        logger.info(f"Procesando mensaje de audio de {user_display}")

        # Paso 1: Descargar el audio
        audio_file_path = await self.telegram_service.download_audio(audio_message.file_id)
        logger.info("PASO 3 - process_audio_message")
        # Paso 2: Transcribir el audio
        transcription = await self.transcription_service.transcribe_audio(audio_file_path)

        # Paso 3: Enviar query al sistema
        session_id = f"telegram-group-{audio_message.chat.chat_id}"
        result = await self.query_service.send_query(transcription, session_id)

        answer = result.get('answer', 'No se obtuvo respuesta')

        await self.telegram_service.send_message(
            f"🎤 Audio: {transcription}\n\n💬 Respuesta: {answer}",
            reply_to_message_id=audio_message.message_id
        )

        # Retornar el path del audio para que el decorador haga cleanup
        return None, audio_file_path


    async def start(self):
        """Inicia el microservicio"""
        try:
            logger.info("=" * 60)
            logger.info("Iniciando Microservicio de Telegram Bot")
            logger.info("=" * 60)

            # Validar configuración
            settings.validate()
            logger.info("Configuracion validada correctamente")

            # Información del bot
            logger.info(f"Chat ID: {settings.TELEGRAM_CHAT_ID}")
            logger.info(f"Intervalo de polling: {settings.POLLING_INTERVAL} segundos")
            logger.info(f"API de transcripcion: {settings.TRANSCRIPTION_API_URL}")
            logger.info(f"Sistema de queries: {settings.QUERY_SYSTEM_URL}")

            # Iniciar polling
            logger.info("\nBot iniciado. Esperando mensajes de audio y texto...\n")
            await self.telegram_service.start_polling(
                self.process_audio_message,
                self.process_text_message
            )

        except ValueError as e:
            logger.error(f"Error de configuracion: {e}")
            logger.error("Por favor, configura las variables de entorno en el archivo .env")
        except KeyboardInterrupt:
            logger.info("\n\nBot detenido por el usuario")
        except Exception as e:
            logger.error(f"Error fatal: {e}")
        finally:
            # Cerrar todas las sesiones de aiohttp
            logger.info("Cerrando conexiones...")
            await self.telegram_service.close()
            await self.transcription_service.close()
            await self.query_service.close()
            logger.info("Conexiones cerradas correctamente")
