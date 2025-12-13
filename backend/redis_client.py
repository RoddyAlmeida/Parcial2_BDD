"""
Cliente Redis - Soporte para Redis local y Upstash Redis (REST API)
"""

import json
import httpx
from typing import Optional, Any
from config import settings

class RedisClient:
    """Cliente Redis que soporta Redis local y Upstash REST API"""
    
    def __init__(self):
        self.is_upstash = settings.is_upstash_redis()
        
        if self.is_upstash:
            # Configuración para Upstash Redis (REST API)
            self.upstash_url = settings.UPSTASH_REDIS_REST_URL
            self.upstash_token = settings.UPSTASH_REDIS_REST_TOKEN
            self.client = None  # No se usa cliente Redis tradicional
        else:
            # Configuración para Redis local
            import redis
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True
            )
    
    def _upstash_request(self, command: str, *args) -> Any:
        """Realizar petición a Upstash Redis REST API"""
        # Upstash REST API: el comando debe ir en el body como primer elemento
        # URL: {REST_URL} (sin el comando)
        # Body: ["COMANDO", "arg1", "arg2", ...]
        url = self.upstash_url
        headers = {
            "Authorization": f"Bearer {self.upstash_token}",
            "Content-Type": "application/json"
        }
        
        # Convertir argumentos a formato Upstash
        # El comando va como primer elemento del array
        body = [command.upper()] + [str(arg) for arg in args]
        
        try:
            with httpx.Client() as client:
                response = client.post(url, headers=headers, json=body, timeout=10.0)
                response.raise_for_status()
                result = response.json()
                # Upstash devuelve {"result": "valor"} donde valor puede ser string, array, etc.
                if isinstance(result, dict) and "result" in result:
                    result_value = result["result"]
                    # Si el resultado es un string que parece JSON, intentar parsearlo
                    if isinstance(result_value, str):
                        # PING devuelve "[]" como string, lo convertimos
                        if result_value == "[]" and command.upper() == "PING":
                            return "PONG"
                        # Intentar parsear si es JSON válido
                        try:
                            import json
                            parsed = json.loads(result_value)
                            return parsed
                        except (json.JSONDecodeError, ValueError):
                            return result_value
                    return result_value
                return result
        except httpx.HTTPError as e:
            raise ConnectionError(f"Error conectando con Upstash Redis: {str(e)}")
    
    def get(self, key: str) -> Optional[str]:
        """Obtener valor de una clave"""
        if self.is_upstash:
            return self._upstash_request("GET", key)
        else:
            return self.client.get(key)
    
    def set(self, key: str, value: str) -> bool:
        """Establecer valor de una clave"""
        if self.is_upstash:
            result = self._upstash_request("SET", key, value)
            return result == "OK"
        else:
            return self.client.set(key, value)
    
    def setex(self, key: str, time: int, value: str) -> bool:
        """Establecer valor con TTL"""
        if self.is_upstash:
            # Upstash usa EX para TTL
            result = self._upstash_request("SET", key, value, "EX", str(time))
            return result == "OK"
        else:
            return self.client.setex(key, time, value)
    
    def delete(self, *keys: str) -> int:
        """Eliminar una o más claves"""
        if self.is_upstash:
            result = self._upstash_request("DEL", *keys)
            return result if isinstance(result, int) else 1
        else:
            return self.client.delete(*keys)
    
    def rpush(self, key: str, *values: str) -> int:
        """Agregar valores al final de una lista"""
        if self.is_upstash:
            result = self._upstash_request("RPUSH", key, *values)
            return result if isinstance(result, int) else len(values)
        else:
            return self.client.rpush(key, *values)
    
    def publish(self, channel: str, message: str) -> int:
        """Publicar mensaje en un canal (Pub/Sub)"""
        if self.is_upstash:
            # Upstash soporta PUBLISH
            result = self._upstash_request("PUBLISH", channel, message)
            return result if isinstance(result, int) else 1
        else:
            return self.client.publish(channel, message)
    
    def ping(self) -> bool:
        """Verificar conexión"""
        if self.is_upstash:
            try:
                result = self._upstash_request("PING")
                return result == "PONG"
            except:
                return False
        else:
            try:
                return self.client.ping()
            except:
                return False
    
    def llen(self, key: str) -> int:
        """Obtener longitud de una lista"""
        if self.is_upstash:
            result = self._upstash_request("LLEN", key)
            return result if isinstance(result, int) else 0
        else:
            return self.client.llen(key)
    
    def lrange(self, key: str, start: int, end: int) -> list:
        """Obtener rango de elementos de una lista"""
        if self.is_upstash:
            result = self._upstash_request("LRANGE", key, str(start), str(end))
            return result if isinstance(result, list) else []
        else:
            return self.client.lrange(key, start, end)

# Instancia global del cliente Redis
redis_client = RedisClient()

