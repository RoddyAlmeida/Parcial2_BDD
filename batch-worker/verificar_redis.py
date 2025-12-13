"""
Script para verificar el estado de las colas Redis
"""

from redis_client import redis_client
from config import settings
import json

print("=" * 60)
print("ESTADO DE COLAS REDIS")
print("=" * 60)
print()

# Verificar conexión
if not redis_client.ping():
    print("[ERROR] No se pudo conectar a Redis")
    exit(1)

    print("[OK] Conexion a Redis establecida")
print()

# Verificar longitudes de colas
cola_principal = settings.COLA_PRINCIPAL
cola_procesadas = settings.COLA_PROCESADAS
cola_fallidas = settings.COLA_FALLIDAS

try:
    pendientes = redis_client.llen(cola_principal)
    procesadas = redis_client.llen(cola_procesadas)
    fallidas = redis_client.llen(cola_fallidas)
    
    print(f"Cola Principal ({cola_principal}):")
    print(f"  Tareas pendientes: {pendientes}")
    print()
    
    print(f"Cola Procesadas ({cola_procesadas}):")
    print(f"  Tareas procesadas: {procesadas}")
    print()
    
    print(f"Cola Fallidas ({cola_fallidas}):")
    print(f"  Tareas fallidas: {fallidas}")
    print()
    
    # Mostrar últimas tareas fallidas
    if fallidas > 0:
        print("=" * 60)
        print("ÚLTIMAS TAREAS FALLIDAS (últimas 3):")
        print("=" * 60)
        try:
            fallidas_list = redis_client.lrange(cola_fallidas, -3, -1)
            for i, tarea_item in enumerate(fallidas_list, 1):
                try:
                    # tarea_item puede venir como string JSON o como dict
                    if isinstance(tarea_item, str):
                        tarea = json.loads(tarea_item)
                    elif isinstance(tarea_item, dict):
                        tarea = tarea_item
                    else:
                        tarea = {"error": "Formato desconocido", "raw": str(tarea_item)}
                    
                    error_msg = tarea.get('error', 'N/A')
                    tarea_info = tarea.get('tarea', {})
                    if isinstance(tarea_info, str):
                        try:
                            tarea_info = json.loads(tarea_info)
                        except:
                            pass
                    tipo = tarea_info.get('tipo', 'N/A') if isinstance(tarea_info, dict) else 'N/A'
                    fecha = tarea.get('procesada_en', 'N/A')
                    
                    print(f"\n{i}. Error: {error_msg}")
                    print(f"   Tipo: {tipo}")
                    print(f"   Fecha: {fecha}")
                except Exception as e:
                    print(f"\n{i}. Error parseando tarea: {e}")
                    print(f"   Tipo del item: {type(tarea_item)}")
                    print(f"   Raw (primeros 200 chars): {str(tarea_item)[:200]}...")
        except Exception as e:
            print(f"Error obteniendo tareas fallidas: {e}")
    
    # Mostrar últimas tareas procesadas
    if procesadas > 0:
        print("\n" + "=" * 60)
        print("ÚLTIMAS TAREAS PROCESADAS (últimas 3):")
        print("=" * 60)
        try:
            procesadas_list = redis_client.lrange(cola_procesadas, -3, -1)
            for i, tarea_str in enumerate(procesadas_list, 1):
                try:
                    tarea = json.loads(tarea_str) if isinstance(tarea_str, str) else tarea_str
                    print(f"\n{i}. Tipo: {tarea.get('tarea', {}).get('tipo', 'N/A')}")
                    print(f"   Estado: {tarea.get('estado', 'N/A')}")
                    print(f"   Fecha: {tarea.get('procesada_en', 'N/A')}")
                except Exception as e:
                    print(f"\n{i}. Error parseando tarea: {e}")
        except Exception as e:
            print(f"Error obteniendo tareas procesadas: {e}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)

