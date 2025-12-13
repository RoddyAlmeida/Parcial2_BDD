"""
Script de prueba para diagnosticar conexión a Upstash Redis
"""

from redis_client import redis_client
from config import settings
import json

print("=" * 60)
print("PRUEBA DE CONEXIÓN A UPSTASH REDIS")
print("=" * 60)
print()

print(f"Upstash URL: {settings.UPSTASH_REDIS_REST_URL}")
print(f"Token configurado: {'Sí' if settings.UPSTASH_REDIS_REST_TOKEN else 'No'}")
print(f"Token (primeros 20 chars): {settings.UPSTASH_REDIS_REST_TOKEN[:20] if settings.UPSTASH_REDIS_REST_TOKEN else 'N/A'}...")
print()

# Probar PING directamente
print("1. Probando PING...")
try:
    import httpx
    
    url = f"{settings.UPSTASH_REDIS_REST_URL}/PING"
    headers = {
        "Authorization": f"Bearer {settings.UPSTASH_REDIS_REST_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"   URL: {url}")
    print(f"   Headers: Authorization: Bearer ***")
    
    with httpx.Client() as client:
        response = client.post(url, headers=headers, json=[], timeout=10.0)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        print(f"   Response Body (raw): {response.text}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   Response JSON: {json.dumps(result, indent=2)}")
                print(f"   Result value: {result.get('result')}")
                print(f"   Result type: {type(result.get('result'))}")
            except Exception as e:
                print(f"   Error parseando JSON: {e}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("2. Probando método ping() del cliente...")
try:
    result = redis_client.ping()
    print(f"   Resultado: {result}")
    print(f"   Tipo: {type(result)}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("3. Probando SET y GET...")
try:
    # Probar SET
    test_key = "test:conexion"
    test_value = "ok"
    result_set = redis_client.set(test_key, test_value)
    print(f"   SET resultado: {result_set}")
    
    # Probar GET
    result_get = redis_client.get(test_key)
    print(f"   GET resultado: {result_get}")
    
    # Limpiar
    redis_client.delete(test_key)
    print(f"   ✅ Operaciones básicas funcionando!")
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

