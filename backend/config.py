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
    # Para permitir todos los orígenes temporalmente, usar: ["*"]
    CORS_ORIGINS: str = '["http://localhost:3000", "https://ticketsyeso.vercel.app"]'
    
    # Opción para permitir todos los orígenes (solo para debug/temporal)
    CORS_ALLOW_ALL: bool = False
    
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
        default_origins = ["http://localhost:3000", "https://ticketsyeso.vercel.app"]
        
        try:
            if isinstance(self.CORS_ORIGINS, str):
                # Limpiar espacios y comillas extra
                cors_str = self.CORS_ORIGINS.strip()
                
                # Si empieza y termina con comillas, quitarlas
                if cors_str.startswith('"') and cors_str.endswith('"'):
                    cors_str = cors_str[1:-1]
                
                # Intentar parsear como JSON
                try:
                    origins = json.loads(cors_str)
                    if isinstance(origins, list):
                        return origins
                except json.JSONDecodeError:
                    # Si falla, intentar separar por comas
                    origins = [o.strip().strip('"').strip("'") for o in cors_str.split(',')]
                    if origins and origins[0]:  # Verificar que no esté vacío
                        return origins
            
            if isinstance(self.CORS_ORIGINS, list):
                return self.CORS_ORIGINS
                
        except Exception as e:
            import logging
            logging.warning(f"Error parseando CORS_ORIGINS: {e}. Usando valores por defecto.")
        
        # Fallback: incluir localhost y dominio de Vercel
        return default_origins
    
    def is_upstash_redis(self) -> bool:
        """Verificar si se está usando Upstash Redis"""
        return bool(self.UPSTASH_REDIS_REST_URL and self.UPSTASH_REDIS_REST_TOKEN)

# Instancia global de configuración
settings = Settings()
