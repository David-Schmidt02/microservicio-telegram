import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración centralizada del microservicio"""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

    # APIs externas
    TRANSCRIPTION_API_URL = os.getenv('TRANSCRIPTION_API_URL')
    #TRANSCRIPTION_API_KEY = os.getenv('TRANSCRIPTION_API_KEY')

    QUERY_SYSTEM_URL = os.getenv('QUERY_SYSTEM_URL')
    #QUERY_SYSTEM_API_KEY = os.getenv('QUERY_SYSTEM_API_KEY')

    # Configuración del polling
    POLLING_INTERVAL = float(os.getenv('POLLING_INTERVAL', 2.5))

    # Configuración de logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls):
        """Valida que todas las configuraciones necesarias estén presentes"""
        required_vars = [
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID',
            'TRANSCRIPTION_API_URL',
            'QUERY_SYSTEM_URL'
        ]

        missing = [var for var in required_vars if not getattr(cls, var)]

        if missing:
            raise ValueError(f"Faltan las siguientes variables de entorno: {', '.join(missing)}")

        return True


settings = Settings()
