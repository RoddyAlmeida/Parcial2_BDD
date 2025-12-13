"""
Cliente Redis - Soporte para Redis local y Upstash Redis (REST API)
Mismo cliente que el backend para consistencia
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
            # Configuraci?n para Upstash Redis (REST API)
            self.upstash_url = settings.UPSTASH_REDIS_REST_URL
            self.upstash_token = settings.UPSTASH_REDIS_REST_TOKEN
            self.client = None  # No se usa cliente Redis tradicional
        else:
            # Configuraci?n para Redis local
            import redis
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD or None,
                decode_responses=True
            )
    
    def _upstash_request(self, command: str, *args) -> Any:
        """Realizar petici?n a Upstash Redis REST API"""
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
                        # Para LPOP, LRANGE, etc., el resultado puede ser un string JSON
                        # que necesita ser parseado, pero tambi?n puede ser un string simple
                        # Solo parsear si parece JSON v?lido y no es un comando que devuelve strings simples
                        if command.upper() in ["LPOP", "LRANGE"]:
                            # Para estos comandos, intentar parsear si es JSON v?lido
                            try:
                                import json
                                # Si el string empieza con [ o {, es probablemente JSON
                                if result_value.strip().startswith(('[', '{')):
                                    parsed = json.loads(result_value)
                                    return parsed
                            except (json.JSONDecodeError, ValueError):
                                pass
                        # Intentar parsear si es JSON v?lido (para otros comandos)
                        try:
                            import json
                            parsed = json.loads(result_value)
                            return parsed
                        except (json.JSONDecodeError, ValueError):
                            return result_value
                    # Si el resultado ya es un dict/list (Upstash lo parse? autom?ticamente)
                    return result_value
                return result
        except httpx.HTTPError as e:
            # Obtener m?s detalles del error
            error_detail = ""
            try:
                if hasattr(e, 'response') and e.response is not None:
                    error_detail = f" - {e.response.text}"
            except:
                pass
            raise ConnectionError(f"Error conectando con Upstash Redis: {str(e)}{error_detail}")
        except Exception as e:
            raise ConnectionError(f"Error procesando respuesta de Upstash: {str(e)}")
    
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
            # Upstash devuelve "OK" como string
            return result == "OK" or (isinstance(result, str) and result.upper() == "OK")
        else:
            return self.client.set(key, value)
    
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
            result = self._upstash_request("PUBLISH", channel, message)
            return result if isinstance(result, int) else 1
        else:
            return self.client.publish(channel, message)
    
    def blpop(self, *keys: str, timeout: int = 0) -> Optional[tuple]:
        """Bloquear y obtener elemento de lista (BLPOP)"""
        if self.is_upstash:
            # Upstash REST API no soporta BLPOP directamente
            # Implementaci?n alternativa: polling con LPOP
            import time
            import json
            start_time = time.time()
            while time.time() - start_time < timeout:
                for key in keys:
                    result = self._upstash_request("LPOP", key)
                    if result:
                        # Upstash puede devolver el resultado como string JSON o como dict/list parseado
                        # Siempre devolver como string JSON para consistencia
                        if isinstance(result, str):
                            # Si ya es string, verificar si es JSON válido
                            try:
                                # Intentar parsear y volver a serializar para normalizar
                                parsed = json.loads(result)
                                return (key, json.dumps(parsed))
                            except (json.JSONDecodeError, ValueError):
                                # Si no es JSON, devolver como está
                                return (key, result)
                        else:
                            # Si viene como dict/list (Upstash lo parseó), serializarlo
                            return (key, json.dumps(result))
                time.sleep(0.5)  # Polling cada 500ms
            return None
        else:
            result = self.client.blpop(keys, timeout=timeout)
            return result if result else None
    
    def ping(self) -> bool:
        """Verificar conexi?n"""
        if self.is_upstash:
            try:
                result = self._upstash_request("PING")
                # Upstash PING devuelve "PONG" despu?s de nuestro procesamiento
                return result == "PONG" or (isinstance(result, str) and result.upper() == "PONG")
            except Exception as e:
                import logging
                logging.error(f"Error en ping a Upstash: {str(e)}")
                return False
        else:
            try:
                return self.client.ping()
            except Exception as e:
                import logging
                logging.error(f"Error en ping a Redis local: {str(e)}")
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
            # Upstash puede devolver el resultado como string JSON o como lista
            if isinstance(result, str):
                try:
                    import json
                    return json.loads(result)
                except:
                    return [result] if result else []
            return result if isinstance(result, list) else []
        else:
            return self.client.lrange(key, start, end)
    
    def keys(self, pattern: str) -> list:
        """Obtener claves que coincidan con un patr?n"""
        if self.is_upstash:
            # Upstash REST API no soporta KEYS directamente
            # Nota: En producci?n, evita usar KEYS, usa SCAN o estructuras de datos espec?ficas
            import logging
            logging.warning("KEYS no est? disponible en Upstash REST API. Considera usar estructuras de datos espec?ficas.")
            return []
        else:
            return self.client.keys(pattern)
    
    def delete(self, *keys: str) -> int:
        """Eliminar una o m?s claves"""
        if self.is_upstash:
            result = self._upstash_request("DEL", *keys)
            return result if isinstance(result, int) else 1
        else:
            return self.client.delete(*keys)

# Instancia global del cliente Redis
redis_client = RedisClient()

