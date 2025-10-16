import os
from typing import cast
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración centralizada del microservicio"""

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN')  # type: ignore
    TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')  # type: ignore

    # APIs externas
    TRANSCRIPTION_API_URL: str = os.getenv('TRANSCRIPTION_API_URL')  # type: ignore
    #TRANSCRIPTION_API_KEY = os.getenv('TRANSCRIPTION_API_KEY')

    QUERY_SYSTEM_URL: str = os.getenv('QUERY_SYSTEM_URL')  # type: ignore
    #QUERY_SYSTEM_API_KEY = os.getenv('QUERY_SYSTEM_API_KEY')

    # Configuración del polling
    POLLING_INTERVAL: float = float(os.getenv('POLLING_INTERVAL', 2.5))

    # Configuración de logs
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')  # type: ignore

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
