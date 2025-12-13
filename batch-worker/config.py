"""
Configuración del Batch Worker
Manejo seguro de variables de entorno
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Configuración del Batch Worker"""
    
    # Supabase Configuration (Usuario Batch)
    SUPABASE_DB_URL_BATCH: Optional[str] = None  # URL completa para usuario batch
    SUPABASE_DB_USER_BATCH: Optional[str] = None
    SUPABASE_DB_PASSWORD_BATCH: Optional[str] = None
    SUPABASE_DB_HOST: Optional[str] = None
    SUPABASE_DB_PORT: Optional[str] = "5432"
    SUPABASE_DB_NAME: Optional[str] = "postgres"
    
    # Fallback: Usar la misma URL del API si no está configurado el batch
    SUPABASE_DB_URL: Optional[str] = None  # URL del API (fallback)
    
    # Redis Configuration (Upstash)
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    
    # Redis Configuration (Local - fallback)
    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[int] = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # Batch Worker Configuration
    COLA_PRINCIPAL: str = "cola:batch:procesar"
    COLA_PROCESADAS: str = "cola:batch:procesadas"
    COLA_FALLIDAS: str = "cola:batch:fallidas"
    TIMEOUT_BLPOP: int = 30  # Segundos
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignorar campos extra en lugar de rechazarlos
    
    def get_database_url(self) -> str:
        """Obtener URL de conexión a la base de datos para usuario batch"""
        # Prioridad 1: URL completa del batch
        if self.SUPABASE_DB_URL_BATCH:
            return self.SUPABASE_DB_URL_BATCH
        
        # Prioridad 2: Construir URL si se proporcionan componentes individuales del batch
        if self.SUPABASE_DB_USER_BATCH and self.SUPABASE_DB_PASSWORD_BATCH and self.SUPABASE_DB_HOST:
            return (
                f"postgresql://{self.SUPABASE_DB_USER_BATCH}:{self.SUPABASE_DB_PASSWORD_BATCH}"
                f"@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
            )
        
        # Prioridad 3: Fallback a URL del API (solo para desarrollo/pruebas)
        if self.SUPABASE_DB_URL:
            import logging
            logging.warning("⚠️  Usando SUPABASE_DB_URL del API como fallback. Para producción, configura SUPABASE_DB_URL_BATCH.")
            return self.SUPABASE_DB_URL
        
        raise ValueError(
            "Se requiere SUPABASE_DB_URL_BATCH o componentes individuales de conexión.\n"
            "Para desarrollo rápido, puedes usar SUPABASE_DB_URL (mismo usuario del API)."
        )
    
    def is_upstash_redis(self) -> bool:
        """Verificar si se está usando Upstash Redis"""
        return bool(self.UPSTASH_REDIS_REST_URL and self.UPSTASH_REDIS_REST_TOKEN)

# Instancia global de configuración
settings = Settings()

