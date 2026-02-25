"""
Módulo de configuración centralizada para la aplicación.
Carga variables de entorno y proporciona configuraciones para diferentes entornos.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Cargar variables de entorno desde .env en la raíz del proyecto
load_dotenv()

@dataclass
class DatabaseConfig:
    """Configuración de base de datos desde variables de entorno."""
    host: str
    port: int
    user: str
    password: str
    database: str
    
    @classmethod
    def from_env(cls):
        """Crea configuración desde variables de entorno con validación."""
        required_vars = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            raise ValueError(
                f"Variables de entorno faltantes: {missing}. "
                "Por favor, crea un archivo .env en la raíz del proyecto basado en .env.example"
            )
        
        return cls(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
    
    @property
    def connection_string(self) -> str:
        """Genera el string de conexión para SQLAlchemy."""
        return (
            f"mysql+pymysql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class Config:
    """Configuración general de la aplicación."""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-cambiar-en-produccion')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
    
    # Database
    DB_CONFIG = DatabaseConfig.from_env()


class DevelopmentConfig(Config):
    """Configuración para desarrollo."""
    FLASK_ENV = 'development'
    FLASK_DEBUG = True


class ProductionConfig(Config):
    """Configuración para producción."""
    FLASK_ENV = 'production'
    FLASK_DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY')  # Obligatorio en producción


# Diccionario de configuraciones por entorno
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}