import asyncio
from src.bot import TelegramAudioBot
from src.utils.logger import setup_logger


logger = setup_logger(__name__)

def main():
    """Función principal"""
    bot = TelegramAudioBot()
    asyncio.run(bot.start())

if __name__ == "__main__":
    main()