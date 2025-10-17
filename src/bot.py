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


    def _get_search_incidents(self, result: dict) -> list:
        """Obtiene los incidentes si es una búsqueda válida del MCP search."""
        if result.get('mcp_server_used') != 'search':
            return []

        metadata = result.get('metadata', {})
        results = metadata.get('results', {})
        return results.get('incidentes', [])


    def _format_incident(self, incidente: dict, numero: int) -> str:
        """Formatea un incidente como mensaje de Telegram."""
        mensaje = f"Incidente {numero}\n\n"
        mensaje += f"Descripción: {incidente.get('descripcion', 'N/A')}\n\n"
        mensaje += f"Fecha y hora: {incidente.get('fecha', 'N/A')} a las {incidente.get('horario_exacto', 'N/A')}\n\n"
        mensaje += f"Ubicación: {incidente.get('direccion', 'N/A')}, Barrio {incidente.get('barrio', 'N/A')}, {incidente.get('comuna', 'N/A')}\n\n"

        if incidente.get('comisaria'):
            mensaje += f"Comisaría: {incidente.get('comisaria')}\n\n"

        if incidente.get('comentarios'):
            mensaje += f"Comentarios adicionales: {incidente.get('comentarios')}\n\n"

        return mensaje


    async def _send_search_incidents(self, incidentes: list, answer: str, reply_to_message_id: int, audio_transcription: str = None):
        """Envía resumen e incidentes de una búsqueda."""
        # Enviar resumen (primeros 80 caracteres del answer)

        resumen = answer[:60]
        if audio_transcription:
            message = f"🎤 Audio: {audio_transcription}\n\n💬 Respuesta: {resumen}"
            await self.telegram_service.send_message(
                message,
                reply_to_message_id=reply_to_message_id
            )
        else:
            await self.telegram_service.send_message(
                resumen,
                reply_to_message_id=reply_to_message_id
            )

        # Enviar cada incidente formateado con su ubicación
        for i, incidente in enumerate(incidentes, 1):
            # Enviar mensaje con la información del incidente
            mensaje = self._format_incident(incidente, i)
            await self.telegram_service.send_message(mensaje)

            # Enviar venue si hay coordenadas disponibles
            latitud = incidente.get('latitud')
            longitud = incidente.get('longitud')

            if latitud and longitud:
                title = f"Incidente {i} - {incidente.get('barrio', 'Sin barrio')}"
                address = f"{incidente.get('direccion', 'Sin dirección')}, {incidente.get('comuna', '')}"

                await self.telegram_service.send_venue(
                    latitude=latitud,
                    longitude=longitud,
                    title=title,
                    address=address
                )


    async def _send_normal_response(self, answer: str, reply_to_message_id: int, audio_transcription: str = None):
        """Envía una respuesta normal sin incidentes."""
        if audio_transcription:
            await self.telegram_service.send_message(
                f"🎤 Audio: {audio_transcription}\n\n💬 Respuesta: {answer}",
                reply_to_message_id=reply_to_message_id
            )
        else:
            await self.telegram_service.send_message(
                f"{answer}",
                reply_to_message_id=reply_to_message_id
            )


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

        # Paso 3: Verificar si hay incidentes de búsqueda
        incidentes = self._get_search_incidents(result)

        # Paso 4: Enviar respuesta según el tipo
        if incidentes:
            await self._send_search_incidents(incidentes, answer, text_message.message_id)
        else:
            await self._send_normal_response(answer, text_message.message_id)


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

        # Paso 4: Obtener la respuesta
        answer = result.get('answer', 'No se obtuvo respuesta')

        # Paso 5: Verificar si hay incidentes de búsqueda
        incidentes = self._get_search_incidents(result)

        # Paso 6: Enviar respuesta según el tipo
        if incidentes:
            
            await self._send_search_incidents(incidentes, answer, audio_message.message_id, transcription)
        else:
            await self._send_normal_response(answer, audio_message.message_id, transcription)

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
