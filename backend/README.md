# Backend - Sistema de Tickets de Soporte

API REST construida con **FastAPI** para la gestión de tickets de soporte técnico. Incluye integración con **Supabase** (PostgreSQL), **Redis** (Upstash o local), y soporte para procesamiento batch asíncrono.

## 📋 Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Arquitectura y Tecnologías](#arquitectura-y-tecnologías)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Modelos de Datos](#modelos-de-datos)
- [Endpoints de la API](#endpoints-de-la-api)
- [CORS y Seguridad](#cors-y-seguridad)
- [Redis y Caché](#redis-y-caché)
- [Base de Datos](#base-de-datos)
- [Integración con Batch Worker](#integración-con-batch-worker)
- [Health Checks](#health-checks)
- [Ejemplos de Uso](#ejemplos-de-uso)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Descripción General

Este backend proporciona una API REST completa para gestionar un sistema de tickets de soporte técnico. Incluye:

- ✅ Gestión de usuarios (CRUD)
- ✅ Gestión de tickets (crear, listar, actualizar estado)
- ✅ Sistema de interacciones/comentarios
- ✅ Caché con Redis para optimización
- ✅ Control de concurrencia con transacciones
- ✅ Integración con batch worker para procesamiento asíncrono
- ✅ CORS configurado para frontend en Vercel
- ✅ Health checks para monitoreo

---

## 🏗️ Arquitectura y Tecnologías

### Stack Tecnológico

- **FastAPI** (v0.115.0+): Framework web moderno y rápido para Python
- **SQLAlchemy** (v2.0.36+): ORM para PostgreSQL
- **Pydantic** (v2.9.0+): Validación de datos y modelos
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **PostgreSQL** (Supabase): Base de datos relacional
- **Redis** (Upstash o local): Sistema de caché y colas
- **Python 3.9+**: Lenguaje de programación

### Arquitectura

```
┌─────────────┐
│   Frontend  │ (Next.js en Vercel)
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   Backend   │ (FastAPI)
│  (Render)   │
└──────┬──────┘
       │
       ├──► PostgreSQL (Supabase)
       │
       ├──► Redis (Upstash)
       │      │
       │      └──► Batch Worker
       │
       └──► Logs y Monitoreo
```

---

## 📦 Requisitos

- **Python** 3.9 o superior
- **PostgreSQL** (Supabase recomendado)
- **Redis** (Upstash recomendado para producción, local para desarrollo)
- **pip** (gestor de paquetes de Python)

---

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
cd backend
```

### 2. Crear entorno virtual (recomendado)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
# Windows
copy env.example .env

# Linux/Mac
cp env.example .env
```

Edita el archivo `.env` con tus credenciales (ver sección [Configuración](#configuración)).

---

## ⚙️ Configuración

### Variables de Entorno

El backend utiliza variables de entorno para la configuración. Todas las variables están definidas en `config.py` y se pueden configurar mediante:

1. Archivo `.env` (desarrollo local)
2. Variables de entorno del sistema (producción)

#### Variables Requeridas

##### Base de Datos (Supabase)

**Opción 1: URL completa (Recomendado)**
```env
SUPABASE_DB_URL=postgresql://user:password@host:port/database
```

**Opción 2: Componentes individuales**
```env
SUPABASE_DB_USER=postgres.xxxxx
SUPABASE_DB_PASSWORD=tu_password
SUPABASE_DB_HOST=aws-0-us-west-2.pooler.supabase.com
SUPABASE_DB_PORT=5432
SUPABASE_DB_NAME=postgres
```

##### Redis (Upstash - Recomendado para producción)

```env
UPSTASH_REDIS_REST_URL=https://tu-instancia.upstash.io
UPSTASH_REDIS_REST_TOKEN=tu_token_aqui
```

##### Redis (Local - Solo para desarrollo)

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Opcional
```

**Nota:** Si no se configuran `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN`, el sistema usará Redis local automáticamente.

##### API

```env
API_HOST=0.0.0.0          # Host del servidor
API_PORT=8000             # Puerto del servidor
DEBUG=True                # Modo debug (False en producción)
```

##### CORS

```env
# Lista de orígenes permitidos (formato JSON array)
CORS_ORIGINS=["http://localhost:3000", "https://ticketsyeso.vercel.app"]

# Opcional: Permitir todos los orígenes (solo para debug/temporal)
CORS_ALLOW_ALL=False
```

**Formato de CORS_ORIGINS:**
- JSON array: `["http://localhost:3000", "https://example.com"]`
- String separado por comas: `"http://localhost:3000, https://example.com"`

---

## 📁 Estructura del Proyecto

```
backend/
├── main.py              # Aplicación principal FastAPI y endpoints
├── config.py            # Configuración y manejo de variables de entorno
├── redis_client.py      # Cliente Redis (soporta Upstash y local)
├── requirements.txt     # Dependencias de Python
├── Procfile             # Configuración para deployment (Render)
├── start.sh             # Script de inicio (Linux/Mac)
├── start.bat            # Script de inicio (Windows)
├── env.example          # Ejemplo de variables de entorno
├── test_connection.py   # Script de prueba de conexión
└── README.md            # Esta documentación
```

---

## 📊 Modelos de Datos

### Modelos Pydantic (Request/Response)

#### UsuarioCreate
```python
{
    "email": "usuario@example.com",  # Email válido (EmailStr)
    "nombre": "Juan Pérez",          # Nombre completo
    "rol": "usuario"                 # Rol: "usuario", "admin", "soporte"
}
```

#### UsuarioResponse
```python
{
    "id": "uuid-string",
    "email": "usuario@example.com",
    "nombre": "Juan Pérez",
    "rol": "usuario",
    "activo": true,
    "fecha_creacion": "2024-01-15T10:30:00Z"
}
```

#### TicketCreate
```python
{
    "usuario_id": "uuid-string",
    "titulo": "Problema con login",
    "descripcion": "No puedo iniciar sesión...",
    "prioridad": "media"  # "baja", "media", "alta", "critica"
}
```

#### TicketResponse
```python
{
    "id": "uuid-string",
    "usuario_id": "uuid-string",
    "titulo": "Problema con login",
    "descripcion": "No puedo iniciar sesión...",
    "estado": "abierto",  # "abierto", "en_proceso", "resuelto", "cerrado"
    "prioridad": "media",
    "fecha_creacion": "2024-01-15T10:30:00Z",
    "fecha_actualizacion": "2024-01-15T10:30:00Z"
}
```

#### InteraccionCreate
```python
{
    "ticket_id": "uuid-string",
    "usuario_id": "uuid-string",  # Opcional
    "tipo": "comentario",        # "comentario", "cambio_estado", "nota_interna"
    "contenido": "Texto de la interacción"
}
```

#### InteraccionResponse
```python
{
    "id": 1,
    "ticket_id": "uuid-string",
    "usuario_id": "uuid-string",  # Puede ser null
    "tipo": "comentario",
    "contenido": "Texto de la interacción",
    "fecha_creacion": "2024-01-15T10:30:00Z"
}
```

---

## 🔌 Endpoints de la API

### Base URL

- **Desarrollo local:** `http://localhost:8000`
- **Producción:** `https://parcial2-bdd-pnsh.onrender.com`

### Documentación Interactiva

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

---

### 👥 Usuarios

#### GET `/usuarios/{usuario_id}`

Obtener un usuario específico por ID (con caché Redis).

**Parámetros:**
- `usuario_id` (path): UUID del usuario

**Respuesta 200:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "usuario@example.com",
    "nombre": "Juan Pérez",
    "rol": "usuario",
    "activo": true,
    "fecha_creacion": "2024-01-15T10:30:00Z"
}
```

**Respuesta 404:**
```json
{
    "detail": "Usuario no encontrado"
}
```

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/usuarios/550e8400-e29b-41d4-a716-446655440000"
```

---

#### POST `/usuarios`

Crear un nuevo usuario.

**Body:**
```json
{
    "email": "nuevo@example.com",
    "nombre": "María García",
    "rol": "usuario"
}
```

**Respuesta 200:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "nuevo@example.com",
    "nombre": "María García",
    "rol": "usuario",
    "activo": true,
    "fecha_creacion": "2024-01-15T10:30:00Z"
}
```

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/usuarios" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nuevo@example.com",
    "nombre": "María García",
    "rol": "usuario"
  }'
```

---

#### GET `/usuarios`

Listar usuarios con paginación y filtros.

**Query Parameters:**
- `skip` (int, opcional): Número de registros a saltar (default: 0)
- `limit` (int, opcional): Número máximo de registros (default: 20)
- `activo` (bool, opcional): Filtrar por estado activo

**Respuesta 200:**
```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "usuario1@example.com",
        "nombre": "Juan Pérez",
        "rol": "usuario",
        "activo": true,
        "fecha_creacion": "2024-01-15T10:30:00Z"
    },
    {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "email": "usuario2@example.com",
        "nombre": "María García",
        "rol": "admin",
        "activo": true,
        "fecha_creacion": "2024-01-15T11:00:00Z"
    }
]
```

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/usuarios?skip=0&limit=10&activo=true"
```

---

### 🎫 Tickets

#### GET `/tickets/{ticket_id}`

Obtener un ticket específico por ID (con caché Redis, TTL: 15 minutos).

**Parámetros:**
- `ticket_id` (path): UUID del ticket

**Respuesta 200:**
```json
{
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "titulo": "Problema con login",
    "descripcion": "No puedo iniciar sesión en la aplicación",
    "estado": "abierto",
    "prioridad": "media",
    "fecha_creacion": "2024-01-15T10:30:00Z",
    "fecha_actualizacion": "2024-01-15T10:30:00Z"
}
```

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/tickets/770e8400-e29b-41d4-a716-446655440000"
```

---

#### POST `/tickets`

Crear un nuevo ticket. Automáticamente envía una tarea a la cola de batch worker.

**Body:**
```json
{
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "titulo": "Problema con login",
    "descripcion": "No puedo iniciar sesión en la aplicación",
    "prioridad": "media"
}
```

**Respuesta 200:**
```json
{
    "id": "770e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "titulo": "Problema con login",
    "descripcion": "No puedo iniciar sesión en la aplicación",
    "estado": "abierto",
    "prioridad": "media",
    "fecha_creacion": "2024-01-15T10:30:00Z",
    "fecha_actualizacion": "2024-01-15T10:30:00Z"
}
```

**Nota:** Este endpoint también:
- Envía una tarea a la cola `cola:batch:procesar` en Redis
- Publica un evento en el canal `canal:batch:eventos` para notificaciones

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "titulo": "Problema con login",
    "descripcion": "No puedo iniciar sesión",
    "prioridad": "media"
  }'
```

---

#### GET `/tickets`

Listar tickets con paginación y filtros.

**Query Parameters:**
- `skip` (int, opcional): Número de registros a saltar (default: 0)
- `limit` (int, opcional): Número máximo de registros (default: 20)
- `estado` (string, opcional): Filtrar por estado ("abierto", "en_proceso", "resuelto", "cerrado")

**Respuesta 200:**
```json
[
    {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
        "titulo": "Problema con login",
        "descripcion": "No puedo iniciar sesión",
        "estado": "abierto",
        "prioridad": "media",
        "fecha_creacion": "2024-01-15T10:30:00Z",
        "fecha_actualizacion": "2024-01-15T10:30:00Z"
    }
]
```

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/tickets?skip=0&limit=10&estado=abierto"
```

---

#### PATCH `/tickets/{ticket_id}/estado`

Actualizar el estado de un ticket con control de concurrencia (bloqueo pesimista).

**Parámetros:**
- `ticket_id` (path): UUID del ticket
- `nuevo_estado` (query): Nuevo estado ("abierto", "en_proceso", "resuelto", "cerrado")
- `usuario_id` (query): UUID del usuario que realiza el cambio

**Respuesta 200:**
```json
{
    "mensaje": "Estado actualizado correctamente",
    "estado": "en_proceso"
}
```

**Respuesta 404:**
```json
{
    "detail": "Ticket no encontrado"
}
```

**Nota:** Este endpoint:
- Usa transacciones con bloqueo pesimista (`FOR UPDATE`)
- Crea automáticamente una interacción de tipo "cambio_estado"
- Invalida el caché del ticket

**Ejemplo:**
```bash
curl -X PATCH "http://localhost:8000/tickets/770e8400-e29b-41d4-a716-446655440000/estado?nuevo_estado=en_proceso&usuario_id=550e8400-e29b-41d4-a716-446655440000"
```

---

### 💬 Interacciones

#### GET `/tickets/{ticket_id}/interacciones`

Obtener todas las interacciones de un ticket (optimizado con índice compuesto).

**Parámetros:**
- `ticket_id` (path): UUID del ticket

**Respuesta 200:**
```json
[
    {
        "id": 1,
        "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
        "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
        "tipo": "comentario",
        "contenido": "He revisado el problema y parece ser un issue de autenticación",
        "fecha_creacion": "2024-01-15T11:00:00Z"
    },
    {
        "id": 2,
        "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
        "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
        "tipo": "cambio_estado",
        "contenido": "Estado actualizado a en_proceso",
        "fecha_creacion": "2024-01-15T11:05:00Z"
    }
]
```

**Nota:** Este endpoint está limitado a 50 interacciones y ordenado por fecha descendente.

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/tickets/770e8400-e29b-41d4-a716-446655440000/interacciones"
```

---

#### POST `/interacciones`

Crear una nueva interacción (comentario, nota, etc.).

**Body:**
```json
{
    "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "tipo": "comentario",
    "contenido": "He revisado el problema y parece ser un issue de autenticación"
}
```

**Respuesta 200:**
```json
{
    "id": 1,
    "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "tipo": "comentario",
    "contenido": "He revisado el problema y parece ser un issue de autenticación",
    "fecha_creacion": "2024-01-15T11:00:00Z"
}
```

**Nota:** Este endpoint invalida automáticamente el caché del ticket.

**Ejemplo:**
```bash
curl -X POST "http://localhost:8000/interacciones" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "tipo": "comentario",
    "contenido": "He revisado el problema"
  }'
```

---

### 🏥 Health Checks

#### GET `/health`

Verificar el estado de todos los servicios (base de datos y Redis).

**Respuesta 200 (OK):**
```json
{
    "status": "ok",
    "timestamp": "2024-01-15T12:00:00Z",
    "services": {
        "redis": "ok",
        "database": "ok"
    }
}
```

**Respuesta 200 (Degradado):**
```json
{
    "status": "degraded",
    "timestamp": "2024-01-15T12:00:00Z",
    "services": {
        "redis": "error: Connection refused",
        "database": "ok"
    }
}
```

**Ejemplo:**
```bash
curl -X GET "http://localhost:8000/health"
```

---

### 🔧 Debug

#### GET `/debug/cors`

Verificar la configuración de CORS.

**Respuesta 200:**
```json
{
    "cors_origins": [
        "http://localhost:3000",
        "https://ticketsyeso.vercel.app"
    ],
    "cors_origins_raw": "[\"http://localhost:3000\",\"https://ticketsyeso.vercel.app\"]",
    "cors_origins_type": "str",
    "message": "Si puedes ver esto desde el navegador, CORS está funcionando",
    "cors_allow_all": false
}
```

---

#### GET `/test-cors`

Endpoint simple para probar CORS desde el frontend.

**Respuesta 200:**
```json
{
    "status": "ok",
    "message": "CORS funcionando correctamente",
    "timestamp": "2024-01-15T12:00:00Z"
}
```

---

## 🔒 CORS y Seguridad

### Configuración de CORS

El backend está configurado para permitir peticiones desde:

1. **Orígenes específicos:** Definidos en `CORS_ORIGINS`
2. **Regex para Vercel:** Cualquier subdominio de `*.vercel.app` (incluye previews)

### Configuración Normal

```python
allow_origins=["http://localhost:3000", "https://ticketsyeso.vercel.app"]
allow_origin_regex=r"https://.*\.vercel\.app"
allow_credentials=True
allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
```

### Modo Debug (Temporal)

Para permitir todos los orígenes temporalmente:

```env
CORS_ALLOW_ALL=True
```

**⚠️ Advertencia:** Solo usar en desarrollo o para debugging. No usar en producción.

---

## 💾 Redis y Caché

### Cliente Redis

El backend soporta dos modos de Redis:

1. **Upstash Redis (REST API)** - Recomendado para producción
2. **Redis Local** - Para desarrollo

El sistema detecta automáticamente qué modo usar basándose en las variables de entorno.

### Estrategia de Caché

#### Usuarios
- **Clave:** `usuario:{usuario_id}:datos`
- **TTL:** 1 hora (3600 segundos)
- **Invalidación:** Al crear/actualizar usuario

#### Tickets
- **Clave:** `ticket:{ticket_id}:completo`
- **TTL:** 15 minutos (900 segundos)
- **Invalidación:** Al actualizar estado o crear interacción

### Colas y Pub/Sub

#### Cola de Batch Worker
- **Cola:** `cola:batch:procesar`
- **Uso:** Enviar tareas asíncronas al batch worker

#### Canal de Eventos
- **Canal:** `canal:batch:eventos`
- **Uso:** Publicar eventos para notificaciones en tiempo real

### Métodos Disponibles

```python
# Obtener valor
redis_client.get("clave")

# Establecer valor
redis_client.set("clave", "valor")

# Establecer con TTL
redis_client.setex("clave", 3600, "valor")

# Eliminar clave
redis_client.delete("clave")

# Agregar a lista
redis_client.rpush("lista", "valor1", "valor2")

# Publicar mensaje
redis_client.publish("canal", "mensaje")

# Verificar conexión
redis_client.ping()
```

---

## 🗄️ Base de Datos

### Esquema de Base de Datos

El backend utiliza las siguientes tablas (definidas en `database/01_ddl_tablas.sql`):

#### `usuarios`
- `id` (UUID, PK)
- `email` (VARCHAR, UNIQUE)
- `nombre` (VARCHAR)
- `rol` (VARCHAR)
- `activo` (BOOLEAN)
- `fecha_creacion` (TIMESTAMP)

#### `tickets`
- `id` (UUID, PK)
- `usuario_id` (UUID, FK → usuarios)
- `titulo` (VARCHAR)
- `descripcion` (TEXT)
- `estado` (VARCHAR)
- `prioridad` (VARCHAR)
- `fecha_creacion` (TIMESTAMP)
- `fecha_actualizacion` (TIMESTAMP)

#### `interacciones`
- `id` (SERIAL, PK)
- `ticket_id` (UUID, FK → tickets)
- `usuario_id` (UUID, FK → usuarios, NULLABLE)
- `tipo` (VARCHAR)
- `contenido` (TEXT)
- `fecha_creacion` (TIMESTAMP)

### Índices

- Índice compuesto en `interacciones(ticket_id, fecha_creacion)` para optimizar consultas
- Índice único en `usuarios(email)`

### Transacciones y Concurrencia

El endpoint `PATCH /tickets/{ticket_id}/estado` utiliza:

- **Bloqueo pesimista:** `SELECT ... FOR UPDATE`
- **Transacciones:** Rollback automático en caso de error
- **Control de concurrencia:** Previene condiciones de carrera

---

## 🔄 Integración con Batch Worker

### Flujo de Trabajo

1. **Crear Ticket** → `POST /tickets`
2. **Backend envía tarea** → Cola Redis `cola:batch:procesar`
3. **Backend publica evento** → Canal `canal:batch:eventos`
4. **Batch Worker procesa** → Notificaciones, reportes, etc.

### Formato de Tarea

```json
{
    "tipo": "notificar_ticket_creado",
    "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### Formato de Evento

```json
{
    "evento": "ticket_creado",
    "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 🏥 Health Checks

### Endpoint `/health`

Verifica el estado de:
- ✅ **Redis:** Conexión y respuesta a PING
- ✅ **Base de Datos:** Ejecuta `SELECT 1` para verificar conexión

**Estados:**
- `ok`: Todos los servicios funcionando
- `degraded`: Al menos un servicio con problemas

---

## 💡 Ejemplos de Uso

### Ejemplo Completo: Crear Ticket y Agregar Comentario

```bash
# 1. Crear usuario
curl -X POST "http://localhost:8000/usuarios" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "cliente@example.com",
    "nombre": "Cliente Ejemplo",
    "rol": "usuario"
  }'

# 2. Crear ticket
curl -X POST "http://localhost:8000/tickets" \
  -H "Content-Type: application/json" \
  -d '{
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "titulo": "Error al iniciar sesión",
    "descripcion": "No puedo iniciar sesión con mi cuenta",
    "prioridad": "alta"
  }'

# 3. Agregar comentario
curl -X POST "http://localhost:8000/interacciones" \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": "770e8400-e29b-41d4-a716-446655440000",
    "usuario_id": "550e8400-e29b-41d4-a716-446655440000",
    "tipo": "comentario",
    "contenido": "He revisado el problema, parece ser un issue de autenticación"
  }'

# 4. Actualizar estado
curl -X PATCH "http://localhost:8000/tickets/770e8400-e29b-41d4-a716-446655440000/estado?nuevo_estado=en_proceso&usuario_id=550e8400-e29b-41d4-a716-446655440000"
```

### Ejemplo con JavaScript (Fetch API)

```javascript
// Crear ticket
const crearTicket = async () => {
  const response = await fetch('https://parcial2-bdd-pnsh.onrender.com/tickets', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      usuario_id: '550e8400-e29b-41d4-a716-446655440000',
      titulo: 'Problema con login',
      descripcion: 'No puedo iniciar sesión',
      prioridad: 'media'
    })
  });
  
  const ticket = await response.json();
  console.log('Ticket creado:', ticket);
};

// Listar tickets
const listarTickets = async () => {
  const response = await fetch('https://parcial2-bdd-pnsh.onrender.com/tickets?estado=abierto&limit=10');
  const tickets = await response.json();
  console.log('Tickets abiertos:', tickets);
};
```

---

## 🚀 Deployment

### Render.com

1. **Crear nuevo Web Service** en Render
2. **Conectar repositorio** (GitHub/GitLab)
3. **Configurar variables de entorno:**
   - `SUPABASE_DB_URL`
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`
   - `CORS_ORIGINS`
   - `DEBUG=False`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Variables de Entorno en Render

```
SUPABASE_DB_URL=postgresql://...
UPSTASH_REDIS_REST_URL=https://...
UPSTASH_REDIS_REST_TOKEN=...
CORS_ORIGINS=["http://localhost:3000", "https://ticketsyeso.vercel.app"]
DEBUG=False
```

### Verificar Deployment

```bash
# Health check
curl https://tu-backend.onrender.com/health

# Test CORS
curl https://tu-backend.onrender.com/test-cors
```

---

## 🔧 Troubleshooting

### Error: "Se requiere SUPABASE_DB_URL o componentes individuales de conexión"

**Causa:** Variables de entorno de base de datos no configuradas.

**Solución:** Configurar `SUPABASE_DB_URL` o los componentes individuales en `.env`.

---

### Error: CORS bloqueado

**Causa:** Origen del frontend no está en la lista de orígenes permitidos.

**Solución:**
1. Verificar `CORS_ORIGINS` en variables de entorno
2. Agregar el dominio del frontend a la lista
3. Verificar con `/debug/cors`

---

### Error: Redis no conecta

**Causa:** Credenciales incorrectas o Redis no disponible.

**Solución:**
1. Verificar `UPSTASH_REDIS_REST_URL` y `UPSTASH_REDIS_REST_TOKEN`
2. Si usas Redis local, verificar que esté corriendo
3. Probar con `redis_client.ping()`

---

### Error: Base de datos no conecta

**Causa:** URL de conexión incorrecta o base de datos no disponible.

**Solución:**
1. Verificar `SUPABASE_DB_URL`
2. Probar conexión con `test_connection.py`
3. Verificar que la base de datos esté accesible desde tu IP

---

### Performance: Consultas lentas

**Causa:** Falta de índices o caché no funcionando.

**Solución:**
1. Verificar que los índices estén creados
2. Verificar que Redis esté funcionando
3. Revisar logs para identificar consultas lentas

---

## 📝 Notas Adicionales

### Logging

El backend utiliza el módulo `logging` de Python. Los logs incluyen:
- Configuración de CORS al iniciar
- Errores de conexión
- Advertencias de configuración

### Validación de Datos

Todos los endpoints utilizan **Pydantic** para validación automática:
- Tipos de datos
- Formatos (emails, UUIDs)
- Valores requeridos

### Manejo de Errores

- **404:** Recurso no encontrado
- **500:** Error interno del servidor
- **422:** Error de validación (Pydantic)

---

## 📚 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Upstash Redis Documentation](https://docs.upstash.com/redis)
- [Supabase Documentation](https://supabase.com/docs)

---

## 📄 Licencia

Este proyecto es parte de un trabajo académico.

---

**Última actualización:** Diciembre 2024

