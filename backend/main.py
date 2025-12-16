"""
FastAPI Server - Sistema de Tickets de Soporte
FASE 2: Integración de Servicios
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timezone
import json
import logging

from config import settings
from redis_client import redis_client

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema de Tickets de Soporte",
    description="API para gestión de tickets con FastAPI, Supabase y Redis",
    version="1.0.0"
)

# Obtener orígenes CORS
cors_origins = settings.get_cors_origins()
logger.info(f"CORS Origins configurados: {cors_origins}")
logger.info(f"CORS_ORIGINS raw value: {settings.CORS_ORIGINS}")
logger.info(f"CORS_ALLOW_ALL: {settings.CORS_ALLOW_ALL}")

# CORS - Configuración
# Si CORS_ALLOW_ALL está activado, permitir todos los orígenes (solo para debug)
if settings.CORS_ALLOW_ALL or "*" in cors_origins:
    logger.warning("⚠️  CORS configurado para permitir TODOS los orígenes (modo debug)")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Permitir todos los orígenes
        allow_credentials=False,  # No se puede usar con allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Configuración normal: orígenes específicos + regex para vercel.app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,  # Orígenes específicos
        allow_origin_regex=r"https://.*\.vercel\.app",  # Cualquier subdominio de vercel.app
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

# Configuración de base de datos (Supabase)
DATABASE_URL = settings.get_database_url()
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia para obtener sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============================================
# MODELOS PYDANTIC
# ============================================

class UsuarioCreate(BaseModel):
    email: EmailStr
    nombre: str
    rol: str

class UsuarioResponse(BaseModel):
    id: str
    email: str
    nombre: str
    rol: str
    activo: bool
    fecha_creacion: datetime

class TicketCreate(BaseModel):
    usuario_id: str
    titulo: str
    descripcion: str
    prioridad: str = "media"

class TicketResponse(BaseModel):
    id: str
    usuario_id: str
    titulo: str
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: datetime
    fecha_actualizacion: datetime

class InteraccionCreate(BaseModel):
    ticket_id: str
    usuario_id: Optional[str] = None
    tipo: str
    contenido: str

class InteraccionResponse(BaseModel):
    id: int
    ticket_id: str
    usuario_id: Optional[str]
    tipo: str
    contenido: str
    fecha_creacion: datetime

# ============================================
# ENDPOINTS - USUARIOS
# ============================================

@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(usuario_id: str, db: Session = Depends(get_db)):
    """Obtener usuario con caché Redis"""
    
    # Intentar obtener de caché
    cache_key = f"usuario:{usuario_id}:datos"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Consultar base de datos
    result = db.execute(
        text("SELECT id, email, nombre, rol, activo, fecha_creacion FROM usuarios WHERE id = :id"),
        {"id": usuario_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario = {
        "id": str(result[0]),
        "email": result[1],
        "nombre": result[2],
        "rol": result[3],
        "activo": result[4],
        "fecha_creacion": result[5]
    }
    
    # Almacenar en caché con TTL de 1 hora
    redis_client.setex(cache_key, 3600, json.dumps(usuario, default=str))
    
    return usuario

@app.post("/usuarios", response_model=UsuarioResponse)
async def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    """Crear nuevo usuario"""
    
    result = db.execute(
        text("""
            INSERT INTO usuarios (email, nombre, rol)
            VALUES (:email, :nombre, :rol)
            RETURNING id, email, nombre, rol, activo, fecha_creacion
        """),
        {"email": usuario.email, "nombre": usuario.nombre, "rol": usuario.rol}
    ).fetchone()
    
    db.commit()
    
    nuevo_usuario = {
        "id": str(result[0]),
        "email": result[1],
        "nombre": result[2],
        "rol": result[3],
        "activo": result[4],
        "fecha_creacion": result[5]
    }
    
    # Invalidar caché si existe
    cache_key = f"usuario:{nuevo_usuario['id']}:datos"
    redis_client.delete(cache_key)
    
    return nuevo_usuario

# ============================================
# ENDPOINTS - TICKETS
# ============================================

@app.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def obtener_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """Obtener ticket con caché Redis"""
    
    # Intentar obtener de caché
    cache_key = f"ticket:{ticket_id}:completo"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Consultar base de datos
    result = db.execute(
        text("""
            SELECT id, usuario_id, titulo, descripcion, estado, prioridad, 
                   fecha_creacion, fecha_actualizacion
            FROM tickets WHERE id = :id
        """),
        {"id": ticket_id}
    ).fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    
    ticket = {
        "id": str(result[0]),
        "usuario_id": str(result[1]),
        "titulo": result[2],
        "descripcion": result[3],
        "estado": result[4],
        "prioridad": result[5],
        "fecha_creacion": result[6],
        "fecha_actualizacion": result[7]
    }
    
    # Almacenar en caché con TTL de 15 minutos
    redis_client.setex(cache_key, 900, json.dumps(ticket, default=str))
    
    return ticket

@app.post("/tickets", response_model=TicketResponse)
async def crear_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """Crear nuevo ticket y enviar tarea a cola de batch"""
    
    result = db.execute(
        text("""
            INSERT INTO tickets (usuario_id, titulo, descripcion, prioridad)
            VALUES (:usuario_id, :titulo, :descripcion, :prioridad)
            RETURNING id, usuario_id, titulo, descripcion, estado, prioridad, 
                      fecha_creacion, fecha_actualizacion
        """),
        {
            "usuario_id": ticket.usuario_id,
            "titulo": ticket.titulo,
            "descripcion": ticket.descripcion,
            "prioridad": ticket.prioridad
        }
    ).fetchone()
    
    db.commit()
    
    nuevo_ticket = {
        "id": str(result[0]),
        "usuario_id": str(result[1]),
        "titulo": result[2],
        "descripcion": result[3],
        "estado": result[4],
        "prioridad": result[5],
        "fecha_creacion": result[6],
        "fecha_actualizacion": result[7]
    }
    
    # Enviar tarea a cola de batch worker
    tarea = {
        "tipo": "notificar_ticket_creado",
        "ticket_id": nuevo_ticket["id"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    redis_client.rpush("cola:batch:procesar", json.dumps(tarea))
    
    # Publicar evento
    evento = {
        "evento": "ticket_creado",
        "ticket_id": nuevo_ticket["id"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    redis_client.publish("canal:batch:eventos", json.dumps(evento))
    
    return nuevo_ticket

@app.patch("/tickets/{ticket_id}/estado")
async def actualizar_estado_ticket(
    ticket_id: str,
    nuevo_estado: str,
    usuario_id: str,
    db: Session = Depends(get_db)
):
    """Actualizar estado de ticket con transacción y control de concurrencia"""
    
    try:
        # Iniciar transacción con bloqueo pesimista
        db.execute(
            text("SELECT * FROM tickets WHERE id = :id FOR UPDATE"),
            {"id": ticket_id}
        )
        
        # Actualizar estado
        result = db.execute(
            text("""
                UPDATE tickets 
                SET estado = :estado, fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = :id
                RETURNING id, estado
            """),
            {"id": ticket_id, "estado": nuevo_estado}
        ).fetchone()
        
        if not result:
            db.rollback()
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        
        # Registrar interacción
        db.execute(
            text("""
                INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
                VALUES (:ticket_id, :usuario_id, 'cambio_estado', :contenido)
            """),
            {
                "ticket_id": ticket_id,
                "usuario_id": usuario_id,
                "contenido": f"Estado actualizado a {nuevo_estado}"
            }
        )
        
        db.commit()
        
        # Invalidar caché
        redis_client.delete(f"ticket:{ticket_id}:completo")
        
        return {"mensaje": "Estado actualizado correctamente", "estado": result[1]}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error en transacción: {str(e)}")

# ============================================
# ENDPOINTS - INTERACCIONES
# ============================================

@app.get("/tickets/{ticket_id}/interacciones", response_model=List[InteraccionResponse])
async def obtener_interacciones(ticket_id: str, db: Session = Depends(get_db)):
    """Obtener interacciones de un ticket (optimizado con índice compuesto)"""
    
    result = db.execute(
        text("""
            SELECT id, ticket_id, usuario_id, tipo, contenido, fecha_creacion
            FROM interacciones
            WHERE ticket_id = :ticket_id
            ORDER BY fecha_creacion DESC
            LIMIT 50
        """),
        {"ticket_id": ticket_id}
    ).fetchall()
    
    interacciones = [
        {
            "id": row[0],
            "ticket_id": str(row[1]),
            "usuario_id": str(row[2]) if row[2] else None,
            "tipo": row[3],
            "contenido": row[4],
            "fecha_creacion": row[5]
        }
        for row in result
    ]
    
    return interacciones

@app.post("/interacciones", response_model=InteraccionResponse)
async def crear_interaccion(interaccion: InteraccionCreate, db: Session = Depends(get_db)):
    """Crear nueva interacción"""
    
    result = db.execute(
        text("""
            INSERT INTO interacciones (ticket_id, usuario_id, tipo, contenido)
            VALUES (:ticket_id, :usuario_id, :tipo, :contenido)
            RETURNING id, ticket_id, usuario_id, tipo, contenido, fecha_creacion
        """),
        {
            "ticket_id": interaccion.ticket_id,
            "usuario_id": interaccion.usuario_id,
            "tipo": interaccion.tipo,
            "contenido": interaccion.contenido
        }
    ).fetchone()
    
    db.commit()
    
    # Invalidar caché del ticket
    redis_client.delete(f"ticket:{interaccion.ticket_id}:completo")
    
    nueva_interaccion = {
        "id": result[0],
        "ticket_id": str(result[1]),
        "usuario_id": str(result[2]) if result[2] else None,
        "tipo": result[3],
        "contenido": result[4],
        "fecha_creacion": result[5]
    }
    
    return nueva_interaccion

# ============================================
# HEALTH CHECK
# ============================================

@app.get("/health")
async def health_check():
    """Verificar estado de servicios"""
    
    health = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # Verificar Redis
    try:
        if redis_client.ping():
            health["services"]["redis"] = "ok"
        else:
            health["services"]["redis"] = "error"
    except Exception as e:
        health["services"]["redis"] = f"error: {str(e)}"
    
    # Verificar Base de Datos
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health["services"]["database"] = "ok"
    except Exception as e:
        health["services"]["database"] = f"error: {str(e)}"
    
    # Determinar estado general
    if any("error" in str(v) for v in health["services"].values()):
        health["status"] = "degraded"
    
    return health

@app.get("/debug/cors")
async def debug_cors():
    """Endpoint de debug para verificar configuración de CORS"""
    return {
        "cors_origins": settings.get_cors_origins(),
        "cors_origins_raw": settings.CORS_ORIGINS,
        "cors_origins_type": type(settings.CORS_ORIGINS).__name__,
        "message": "Si puedes ver esto desde el navegador, CORS está funcionando"
    }

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    """Handler explícito para requests OPTIONS (preflight)"""
    return {"message": "OK"}

@app.get("/tickets")
async def listar_tickets(
    skip: int = 0,
    limit: int = 20,
    estado: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Listar tickets con paginación y filtros"""
    
    query = "SELECT id, usuario_id, titulo, descripcion, estado, prioridad, fecha_creacion, fecha_actualizacion FROM tickets WHERE 1=1"
    params = {}
    
    if estado:
        query += " AND estado = :estado"
        params["estado"] = estado
    
    query += " ORDER BY fecha_creacion DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params).fetchall()
    
    tickets = [
        {
            "id": str(row[0]),
            "usuario_id": str(row[1]),
            "titulo": row[2],
            "descripcion": row[3],
            "estado": row[4],
            "prioridad": row[5],
            "fecha_creacion": row[6],
            "fecha_actualizacion": row[7]
        }
        for row in result
    ]
    
    return tickets

@app.get("/usuarios")
async def listar_usuarios(
    skip: int = 0,
    limit: int = 20,
    activo: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Listar usuarios con paginación y filtros"""
    
    query = "SELECT id, email, nombre, rol, activo, fecha_creacion FROM usuarios WHERE 1=1"
    params = {}
    
    if activo is not None:
        query += " AND activo = :activo"
        params["activo"] = activo
    
    query += " ORDER BY fecha_creacion DESC LIMIT :limit OFFSET :skip"
    params["limit"] = limit
    params["skip"] = skip
    
    result = db.execute(text(query), params).fetchall()
    
    usuarios = [
        {
            "id": str(row[0]),
            "email": row[1],
            "nombre": row[2],
            "rol": row[3],
            "activo": row[4],
            "fecha_creacion": row[5]
        }
        for row in result
    ]
    
    return usuarios

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        reload=settings.DEBUG
    )

