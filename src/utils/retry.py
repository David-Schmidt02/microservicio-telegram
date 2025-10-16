"""
Utilidad para manejar reintentos en llamadas async
"""
import asyncio
from typing import TypeVar, Callable, Any
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

T = TypeVar('T')


async def retry_async(
    func: Callable[..., Any],
    *args,
    retries: int = 0,
    delay: float = 1.0,
    backoff: float = 2.0,
    **kwargs
) -> T:
    """
    Ejecuta una función async con reintentos.

    Args:
        func: Función async a ejecutar
        *args: Argumentos posicionales para la función
        retries: Número de reintentos (default: 0 = sin reintentos)
        delay: Tiempo de espera inicial entre reintentos en segundos (default: 1.0)
        backoff: Multiplicador para el delay en cada reintento (default: 2.0)
        **kwargs: Argumentos con nombre para la función

    Returns:
        El resultado de la función

    Raises:
        La última excepción si se agotan los reintentos
    """
    last_exception = None
    current_delay = delay

    for attempt in range(retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if attempt < retries:
                logger.warning(
                    f"Intento {attempt + 1}/{retries + 1} falló para {func.__name__}: {e}. "
                    f"Reintentando en {current_delay}s..."
                )
                await asyncio.sleep(current_delay)
                current_delay *= backoff
            else:
                logger.error(f"Todos los intentos fallaron para {func.__name__}: {e}")
                raise last_exception

    # Esto no debería ejecutarse nunca, pero por si acaso
    if last_exception:
        raise last_exception
