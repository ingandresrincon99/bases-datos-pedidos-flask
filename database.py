"""
Módulo centralizado de conexión a base de datos.
Proporciona una interfaz unificada para SQLAlchemy compatible con pandas.
"""
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config import DatabaseConfig


class DatabaseConnection:
    """
    Manejador de conexiones a base de datos con soporte para context manager.
    Compatible con pandas pd.read_sql().
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        Inicializa la conexión con configuración opcional.
        
        Args:
            config: Configuración de base de datos. Si es None, usa variables de entorno.
        """
        self.config = config or DatabaseConfig.from_env()
        self._engine: Optional[Engine] = None
    
    def __enter__(self):
        """Establece conexión al entrar en context manager."""
        self._engine = create_engine(
            self.config.connection_string,
            pool_size=5,
            pool_recycle=3600,
            pool_pre_ping=True
        )
        return self._engine
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cierra conexión al salir del context manager."""
        if self._engine:
            self._engine.dispose()
    
    @contextmanager
    def get_connection(self) -> Generator[Engine, None, None]:
        """
        Context manager alternativo para obtener conexión.
        
        Yields:
            Engine de SQLAlchemy para usar con pandas
        """
        engine = create_engine(self.config.connection_string)
        try:
            yield engine
        finally:
            engine.dispose()
    
    @property
    def engine(self) -> Engine:
        """Retorna el engine (crea uno nuevo si no existe)."""
        if not self._engine:
            self._engine = create_engine(self.config.connection_string)
        return self._engine
    
    def test_connection(self) -> bool:
        """Prueba la conexión a la base de datos."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            print(f"Error de conexión: {e}")
            return False


# Instancia global para reutilización
db = DatabaseConnection()