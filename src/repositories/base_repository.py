"""Repositorio base abstracto para implementaciones futuras"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """Interfaz base para repositorios. Permite cambiar implementación fácilmente."""

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """Obtiene una entidad por su ID"""
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        """Obtiene todas las entidades"""
        pass

    @abstractmethod
    def save(self, entity: T) -> T:
        """Guarda o actualiza una entidad"""
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Elimina una entidad por su ID"""
        pass

    @abstractmethod
    def exists(self, id: int) -> bool:
        """Verifica si existe una entidad con el ID dado"""
        pass
