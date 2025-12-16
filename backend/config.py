"""
Configuración del Backend
Manejo seguro de variables de entorno
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional
import json

class Settings(BaseSettings):
    """Configuración de la aplicación"""
    
    # Supabase Configuration
    SUPABASE_DB_URL: Optional[str] = None
    SUPABASE_DB_USER: Optional[str] = None
    SUPABASE_DB_PASSWORD: Optional[str] = None
    SUPABASE_DB_HOST: Optional[str] = None
    SUPABASE_DB_PORT: Optional[str] = "5432"
    SUPABASE_DB_NAME: Optional[str] = "postgres"
    
    # Redis Configuration (Upstash)
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None
    
    # Redis Configuration (Local - fallback)
    REDIS_HOST: Optional[str] = "localhost"
    REDIS_PORT: Optional[int] = 6379
    REDIS_PASSWORD: Optional[str] = None
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS - Acepta string JSON o lista
    # Incluye localhost para desarrollo y dominio de Vercel para producción
    CORS_ORIGINS: str = '["http://localhost:3000", "https://ticketsyeso.vercel.app"]'
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"
    
    def get_database_url(self) -> str:
        """Obtener URL de conexión a la base de datos"""
        if self.SUPABASE_DB_URL:
            return self.SUPABASE_DB_URL
        
        if self.SUPABASE_DB_USER and self.SUPABASE_DB_PASSWORD and self.SUPABASE_DB_HOST:
            return (
                f"postgresql://{self.SUPABASE_DB_USER}:{self.SUPABASE_DB_PASSWORD}"
                f"@{self.SUPABASE_DB_HOST}:{self.SUPABASE_DB_PORT}/{self.SUPABASE_DB_NAME}"
            )
        
        raise ValueError("Se requiere SUPABASE_DB_URL o componentes individuales de conexión")
    
    def get_cors_origins(self) -> list:
        """Parsear CORS_ORIGINS como lista"""
        try:
            if isinstance(self.CORS_ORIGINS, str):
                return json.loads(self.CORS_ORIGINS)
            return self.CORS_ORIGINS
        except:
            # Fallback: incluir localhost y dominio de Vercel
            return ["http://localhost:3000", "https://ticketsyeso.vercel.app"]
    
    def is_upstash_redis(self) -> bool:
        """Verificar si se está usando Upstash Redis"""
        return bool(self.UPSTASH_REDIS_REST_URL and self.UPSTASH_REDIS_REST_TOKEN)

# Instancia global de configuración
settings = Settings()
