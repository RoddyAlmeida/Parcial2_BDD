"""
Batch Worker - Procesamiento Asíncrono de Tareas
FASE 2: Integración de Servicios
"""

import json
import time
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

from config import settings
from redis_client import redis_client

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración de base de datos (Supabase) - Usuario Batch
DATABASE_URL = settings.get_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=3, max_overflow=5)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================

def procesar_ticket_creado(tarea: dict, db):
    """Procesar notificación de ticket creado"""
    # Asegurarse de que tarea es un dict
    if isinstance(tarea, str):
        import json
        tarea = json.loads(tarea)
    
    ticket_id = tarea.get("ticket_id")
    logger.info(f"Procesando notificación de ticket creado: {ticket_id}")
    
    # Ejecutar procedimiento almacenado (si existe)
    # db.execute(text("CALL procesar_ticket_creado(:ticket_id)"), {"ticket_id": ticket_id})
    
    # O realizar operaciones específicas
    result = db.execute(
        text("SELECT id, titulo, estado FROM tickets WHERE id = :id"),
        {"id": ticket_id}
    ).fetchone()
    
    if result:
        logger.info(f"Ticket procesado: {result[1]} - Estado: {result[2]}")
    else:
        logger.warning(f"Ticket {ticket_id} no encontrado en la base de datos")
    
    db.commit()

def procesar_tickets_vencidos(tarea: dict, db):
    """Procesar tickets vencidos usando procedimiento almacenado"""
    # Asegurarse de que tarea es un dict
    if isinstance(tarea, str):
        import json
        tarea = json.loads(tarea)
    
    logger.info("Ejecutando procedimiento: procesar_tickets_vencidos")
    
    # Ejecutar procedimiento almacenado
    result = db.execute(
        text("SELECT * FROM procesar_tickets_vencidos()")
    ).fetchall()
    
    tickets_vencidos = []
    for row in result:
        tickets_vencidos.append({
            "ticket_id": str(row[0]),
            "dias_abierto": row[1],
            "estado_actual": row[2]
        })
    
    logger.info(f"Encontrados {len(tickets_vencidos)} tickets vencidos")
    
    # Publicar resultado
    redis_client.publish(
        "canal:batch:eventos",
        json.dumps({
            "evento": "tickets_vencidos_procesados",
            "cantidad": len(tickets_vencidos),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    )
    
    return tickets_vencidos

def generar_reporte(tarea: dict, db):
    """Generar reporte de estadísticas"""
    # Asegurarse de que tarea es un dict
    if isinstance(tarea, str):
        import json
        tarea = json.loads(tarea)
    
    fecha = tarea.get("fecha", datetime.now().strftime("%Y-%m-%d"))
    logger.info(f"Generando reporte para fecha: {fecha}")
    
    # Consultar estadísticas (solo SELECT permitido para rol_batch)
    stats = db.execute(
        text("""
            SELECT 
                estado,
                COUNT(*) as cantidad
            FROM tickets
            WHERE DATE(fecha_creacion) = :fecha
            GROUP BY estado
        """),
        {"fecha": fecha}
    ).fetchall()
    
    reporte = {row[0]: row[1] for row in stats}
    logger.info(f"Reporte generado: {reporte}")
    
    return reporte

def limpiar_cache(tarea: dict):
    """Limpiar caché según patrón"""
    # Asegurarse de que tarea es un dict
    if isinstance(tarea, str):
        import json
        tarea = json.loads(tarea)
    
    patron = tarea.get("patron", "ticket:*")
    logger.info(f"Limpiando caché con patrón: {patron}")
    
    # Nota: Upstash REST API no soporta KEYS directamente
    # En producción, usa estructuras de datos específicas o listas de claves
    claves_especificas = tarea.get("claves", [])
    
    if claves_especificas:
        deleted = redis_client.delete(*claves_especificas)
        logger.info(f"Eliminadas {deleted} claves de caché")
    else:
        logger.warning("No se proporcionaron claves específicas para eliminar. Upstash REST API no soporta KEYS.")

# ============================================
# ROUTER DE TAREAS
# ============================================

def procesar_tarea(tarea_data):
    """Procesar una tarea de la cola"""
    try:
        # tarea_data puede venir como string JSON o como dict (dependiendo de cómo Redis lo devuelva)
        if isinstance(tarea_data, str):
            tarea = json.loads(tarea_data)
        elif isinstance(tarea_data, dict):
            tarea = tarea_data
        else:
            raise ValueError(f"Formato de tarea no válido: {type(tarea_data)}")
        
        tipo = tarea.get("tipo")
        
        logger.info(f"Procesando tarea tipo: {tipo}")
        
        db = SessionLocal()
        try:
            if tipo == "notificar_ticket_creado":
                procesar_ticket_creado(tarea, db)
            
            elif tipo == "procesar_tickets_vencidos":
                procesar_tickets_vencidos(tarea, db)
            
            elif tipo == "generar_reporte":
                generar_reporte(tarea, db)
            
            elif tipo == "limpiar_cache":
                limpiar_cache(tarea)
            
            else:
                logger.warning(f"Tipo de tarea desconocido: {tipo}")
            
            # Marcar tarea como procesada
            tarea_procesada = {
                "tarea": tarea,
                "procesada_en": datetime.now(timezone.utc).isoformat(),
                "estado": "exitoso"
            }
            redis_client.rpush(settings.COLA_PROCESADAS, json.dumps(tarea_procesada))
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Error procesando tarea: {str(e)}", exc_info=True)
        
        # Registrar tarea fallida
        # Asegurarse de que tarea_data sea serializable como dict
        try:
            if isinstance(tarea_data, str):
                tarea_dict = json.loads(tarea_data)
            elif isinstance(tarea_data, dict):
                tarea_dict = tarea_data
            else:
                tarea_dict = {"raw": str(tarea_data)}
        except:
            tarea_dict = {"raw": str(tarea_data)}
        
        tarea_fallida = {
            "tarea": tarea_dict,
            "error": str(e),
            "procesada_en": datetime.now(datetime.timezone.utc).isoformat(),
            "estado": "fallido"
        }
        redis_client.rpush(settings.COLA_FALLIDAS, json.dumps(tarea_fallida))

# ============================================
# LOOP PRINCIPAL
# ============================================

def main():
    """Loop principal del Batch Worker"""
    logger.info("=" * 50)
    logger.info("Iniciando Batch Worker...")
    logger.info("=" * 50)
    
    if settings.is_upstash_redis():
        logger.info(f"Redis: Upstash (REST API)")
        logger.info(f"URL: {settings.UPSTASH_REDIS_REST_URL}")
    else:
        logger.info(f"Redis: Local")
        logger.info(f"Host: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    # Verificar conexión a Redis
    logger.info("🔍 Verificando conexión a Redis...")
    try:
        if redis_client.ping():
            logger.info("✅ Conexión a Redis establecida")
        else:
            logger.error("❌ No se pudo conectar a Redis. Verifica tu configuración.")
            logger.error("   Verifica que UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN estén correctos")
            return
    except Exception as e:
        logger.error(f"❌ Error verificando conexión a Redis: {str(e)}")
        logger.error("   Verifica que UPSTASH_REDIS_REST_URL y UPSTASH_REDIS_REST_TOKEN estén correctos")
        return
    
    logger.info(f"✅ Conexión a Redis establecida")
    logger.info(f"Cola principal: {settings.COLA_PRINCIPAL}")
    logger.info(f"Timeout BLPOP: {settings.TIMEOUT_BLPOP} segundos")
    logger.info("=" * 50)
    
    while True:
        try:
            # Bloquear esperando tarea (BLPOP)
            resultado = redis_client.blpop(settings.COLA_PRINCIPAL, timeout=settings.TIMEOUT_BLPOP)
            
            if resultado:
                cola, tarea_data = resultado
                logger.info(f"📥 Tarea recibida de cola: {cola}")
                procesar_tarea(tarea_data)
            else:
                # Timeout - no hay tareas, continuar esperando
                logger.debug("⏳ Esperando tareas...")
                
        except KeyboardInterrupt:
            logger.info("\n" + "=" * 50)
            logger.info("Deteniendo Batch Worker...")
            logger.info("=" * 50)
            break
        except Exception as e:
            logger.error(f"❌ Error en loop principal: {str(e)}", exc_info=True)
            time.sleep(5)  # Esperar antes de reintentar

if __name__ == "__main__":
    main()

