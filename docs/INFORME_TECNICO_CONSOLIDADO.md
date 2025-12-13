# Informe Técnico Consolidado
## Práctica de Implementación y Administración de la Arquitectura de Datos

**Nivel:** 6to Semestre - Ingeniería en Tecnologías de la Información  
**Arquitectura:** Next.js + FastAPI + Batch Worker + Supabase + Redis

---

## Índice

1. [Fase 1: Diseño Físico, Almacenamiento y Seguridad](#fase-1)
2. [Fase 2: Integración de Servicios, Concurrencia y Recuperación](#fase-2)
3. [Fase 3: Monitorización y Ajuste (Tuning)](#fase-3)
4. [Scripts y Código](#scripts)

---

## FASE 1: Diseño Físico, Almacenamiento y Seguridad {#fase-1}

### 1.1 Diseño Físico y Optimización de Almacenamiento

#### Tablas Diseñadas

**Tabla: usuarios**
- **Justificación:**
  - `id UUID`: Identificador único que evita colisiones y mejora seguridad
  - `email VARCHAR(255) UNIQUE`: Autenticación y búsqueda rápida
  - `nombre VARCHAR(100)`: Suficiente para nombres completos
  - `rol VARCHAR(20) CHECK`: Control de valores válidos (admin, operador, usuario)
  - `activo BOOLEAN`: Soft delete para mantener integridad referencial
  - `fecha_creacion` y `fecha_actualizacion TIMESTAMP`: Auditoría y tracking

**Tabla: tickets**
- **Justificación:**
  - `id UUID`: Identificador único
  - `usuario_id UUID FK`: Relación con usuarios (ON DELETE RESTRICT)
  - `titulo VARCHAR(200)`: Títulos descriptivos
  - `descripcion TEXT`: Sin límite para descripciones largas
  - `estado VARCHAR(20) CHECK`: Control de estados válidos
  - `prioridad VARCHAR(10) CHECK`: Clasificación de urgencia
  - `fecha_cierre TIMESTAMP NULL`: Permite tickets abiertos

**Tabla: interacciones** (Tabla más grande)
- **Justificación:**
  - `id BIGSERIAL`: Más eficiente que UUID en tablas de alto volumen
  - `ticket_id UUID FK`: Relación con tickets (ON DELETE CASCADE)
  - `usuario_id UUID FK NULL`: Permite interacciones del sistema
  - `tipo VARCHAR(20) CHECK`: Clasificación de interacciones
  - `contenido TEXT`: Mensajes largos
  - `metadata JSONB`: Datos estructurados adicionales
  - `fecha_creacion TIMESTAMP`: Crítico para ordenamiento

#### Estrategia de Índices

**Índice Compuesto Non-Clustered: `idx_interacciones_ticket_fecha`**

```sql
CREATE INDEX idx_interacciones_ticket_fecha 
    ON interacciones(ticket_id, fecha_creacion DESC);
```

**Justificación del Índice Compuesto:**

1. **Optimización de Consultas Frecuentes:**
   - Consultas que filtran por `ticket_id` (muy frecuente)
   - Ordenamiento por `fecha_creacion` dentro de cada ticket
   - Combinación de ambos criterios en una sola operación

2. **Mejoras de Rendimiento:**
   - **Reducción de búsquedas secuenciales:** En tablas grandes, evita escaneo completo
   - **Acceso directo:** Permite acceso directo a interacciones de un ticket ordenadas
   - **JOINs optimizados:** Facilita JOINs eficientes con la tabla tickets
   - **Paginación eficiente:** Permite LIMIT/OFFSET sin ordenar toda la tabla

3. **Ejemplo de Consulta Optimizada:**
   ```sql
   SELECT * FROM interacciones 
   WHERE ticket_id = 'xxx' 
   ORDER BY fecha_creacion DESC
   LIMIT 20;
   ```
   Sin índice: Escaneo completo de la tabla (O(n))
   Con índice: Búsqueda directa + ordenamiento parcial (O(log n))

**Índices Adicionales:**
- `idx_interacciones_usuario_id`: Búsquedas por usuario
- `idx_interacciones_tipo`: Filtrado por tipo de interacción
- `idx_interacciones_metadata GIN`: Búsquedas en JSONB

### 1.2 Hardening y Gestión de Usuarios

#### Roles Creados

**ROL_API (usuario_api):**
- **Permisos:** SELECT, INSERT, UPDATE
- **Restricciones:** DENY DELETE
- **Uso:** Servidor FastAPI para operaciones normales

**ROL_BATCH (usuario_batch):**
- **Permisos:** SELECT, EXECUTE (sobre procedimientos)
- **Restricciones:** DENY INSERT, UPDATE, DELETE
- **Uso:** Batch Worker para procesamiento asíncrono

#### Scripts de Seguridad

Ver archivo: `database/02_dcl_roles_permisos.sql`

**Principios de Seguridad:**
- Principio de menor privilegio
- Separación de responsabilidades
- Auditoría mediante roles específicos

---

## FASE 2: Integración de Servicios, Concurrencia y Recuperación {#fase-2}

### 2.1 Control de Concurrencia y Transacciones

#### Niveles de Aislamiento

**READ COMMITTED (Nivel por defecto):**
- Permite lectura de datos confirmados
- No previene lecturas no repetibles
- Mejor rendimiento, menor overhead
- Uso: Operaciones normales del API

**SERIALIZABLE (Máximo aislamiento):**
- Garantiza ejecución secuencial de transacciones
- Previene lecturas sucias, no repetibles y fantasma
- Mayor overhead, riesgo de deadlocks
- Uso: Operaciones críticas de consistencia

#### Problemas de Concurrencia

**Lectura Sucia (Dirty Read):**
- **Escenario:** Transacción lee datos no confirmados de otra transacción
- **Prevención:** PostgreSQL usa READ COMMITTED mínimo (no permite dirty reads)

**Pérdida de Actualización (Lost Update):**
- **Escenario:** Dos transacciones actualizan el mismo registro simultáneamente
- **Solución:** `SELECT FOR UPDATE` para bloqueo pesimista
- **Implementación:** Ver `database/03_transacciones_concurrencia.sql`

#### Scripts de Transacciones

Ver archivo: `database/03_transacciones_concurrencia.sql`

**Ejemplo de Transacción con Bloqueo:**
```sql
BEGIN TRANSACTION;
SELECT * FROM tickets WHERE id = 'xxx' FOR UPDATE;
UPDATE tickets SET estado = 'en_proceso' WHERE id = 'xxx';
INSERT INTO interacciones (...) VALUES (...);
COMMIT;
```

### 2.2 Administración de Redis como Caché y Queue

#### Cacheo de Datos

**Comandos Principales:**
```redis
# Almacenar con TTL
SET usuario:123:datos '{"datos":"..."}' EX 3600

# Consultar métricas
INFO memory
MEMORY STATS
```

**Estrategia de Caché:**
- Usuarios: TTL 1 hora (3600 segundos)
- Tickets: TTL 15 minutos (900 segundos)
- Invalidación automática en actualizaciones

#### Colas para Batch Worker

**Comandos:**
```redis
# Enviar tarea
RPUSH cola:batch:procesar '{"tipo":"procesar_ticket",...}'

# Publicar evento
PUBLISH canal:batch:eventos '{"evento":"ticket_creado",...}'

# Consumir tarea (Batch Worker)
BLPOP cola:batch:procesar 30
```

**Reducción de Carga sobre Supabase:**
1. **Caché de consultas frecuentes:** Reduce SELECT repetitivos
2. **Procesamiento asíncrono:** Batch Worker no bloquea API
3. **Pub/Sub:** Notificaciones sin polling
4. **Contadores en tiempo real:** Sin UPDATE costosos

Ver documentación completa: `redis/01_cache_comandos.md`

### 2.3 Estrategia de Recuperación

#### Plan de Backup (RPO < 15 minutos)

**Backup Completo:**
- Frecuencia: Diario a las 2:00 AM
- Retención: 30 días
- Método: `pg_dump` completo

**Backup Diferencial:**
- Frecuencia: Cada 6 horas
- Retención: 7 días
- Base: Último backup completo

**Backup de Logs Transaccionales (WAL):**
- Frecuencia: Cada 10 minutos
- Retención: 24 horas
- Crítico para RPO < 15 min

#### Procedimiento de Recuperación Puntual

1. Restaurar backup completo más reciente antes del punto objetivo
2. Restaurar backup diferencial (si aplica)
3. Aplicar logs WAL hasta el timestamp objetivo
4. Verificar integridad con `VACUUM ANALYZE`

#### Mantenimiento

**Reconstrucción de Índices:**
```sql
REINDEX INDEX CONCURRENTLY idx_interacciones_ticket_fecha;
```

**Verificación de Integridad:**
```sql
VACUUM ANALYZE interacciones;
```

**Actualización de Estadísticas:**
```sql
ANALYZE interacciones;
```

Ver scripts completos: `database/04_estrategia_backup.sql`

---

## FASE 3: Monitorización y Ajuste (Tuning) {#fase-3}

### 3.1 Monitoreo de Rendimiento

#### Métricas Críticas de Supabase (PostgreSQL)

| Métrica | Valor Deficiente | Significado | Acción de Tuning |
|---------|------------------|-------------|------------------|
| **Tiempo de respuesta de consultas** | > 1 segundo | Consultas lentas afectan UX | Revisar índices, optimizar queries, considerar particionamiento |
| **Cache hit ratio** | < 90% | Muchas lecturas de disco | Aumentar `shared_buffers`, optimizar consultas frecuentes |
| **Dead tuples** | > 20% de tabla | Fragmentación y espacio desperdiciado | Ejecutar `VACUUM` más frecuentemente, considerar `VACUUM FULL` |
| **Conexiones activas** | > 80% del máximo | Riesgo de saturación | Optimizar pool de conexiones, revisar conexiones inactivas |
| **Tamaño de WAL** | Crecimiento constante | Logs no se archivan correctamente | Verificar `archive_command`, aumentar frecuencia de backups |
| **Índices no utilizados** | > 10 índices | Overhead de mantenimiento | Eliminar índices no usados con `DROP INDEX` |

#### Métricas Críticas de Redis

| Métrica | Valor Deficiente | Significado | Acción de Tuning |
|---------|------------------|-------------|------------------|
| **Uso de memoria** | > 80% de maxmemory | Riesgo de evicción de claves | Aumentar `maxmemory`, implementar TTL más agresivo, revisar claves grandes |
| **Cache hit rate** | < 70% | Muchas consultas a BD | Revisar estrategia de caché, aumentar TTL, pre-cachear datos frecuentes |
| **Latencia de comandos** | > 10ms | Redis lento | Revisar red, considerar Redis Cluster, optimizar comandos |
| **Claves expiradas** | Bajo número | TTL no configurado | Implementar TTL en todas las claves de caché |
| **Longitud de colas** | > 1000 tareas | Batch Worker no procesa rápido | Aumentar workers, optimizar procesamiento, revisar bottlenecks |
| **Fragmentación de memoria** | > 1.5 | Memoria fragmentada | Ejecutar `MEMORY PURGE`, considerar restart con `save` |

### 3.2 Acciones de Tuning Recomendadas

#### Para Supabase:
1. **Monitorear consultas lentas:**
   ```sql
   SELECT query, mean_exec_time, calls 
   FROM pg_stat_statements 
   ORDER BY mean_exec_time DESC 
   LIMIT 10;
   ```

2. **Optimizar índices:**
   - Revisar índices no utilizados
   - Crear índices para consultas frecuentes
   - Reconstruir índices fragmentados

3. **Ajustar configuración:**
   - `shared_buffers`: 25% de RAM
   - `work_mem`: Ajustar según consultas complejas
   - `maintenance_work_mem`: Para VACUUM y CREATE INDEX

#### Para Redis:
1. **Configurar política de evicción:**
   ```
   CONFIG SET maxmemory-policy allkeys-lru
   ```

2. **Monitorear claves grandes:**
   ```redis
   MEMORY USAGE clave:grande
   ```

3. **Optimizar TTL:**
   - Usuarios: 1 hora
   - Tickets: 15 minutos
   - Estadísticas: 5 minutos

---

## Scripts y Código {#scripts}

### Estructura del Proyecto

```
Actividad_BDD/
├── database/
│   ├── 01_ddl_tablas.sql          # DDL: Tablas e índices
│   ├── 02_dcl_roles_permisos.sql  # DCL: Roles y permisos
│   ├── 03_transacciones_concurrencia.sql  # Transacciones
│   └── 04_estrategia_backup.sql   # Estrategia de backup
├── redis/
│   ├── 01_cache_comandos.md       # Documentación Redis
│   └── 02_scripts_redis.sh         # Scripts de ejemplo
├── backend/
│   ├── main.py                    # FastAPI Server
│   └── requirements.txt           # Dependencias Python
├── batch-worker/
│   ├── main.py                    # Batch Worker
│   └── requirements.txt           # Dependencias
├── frontend/
│   ├── pages/index.js             # Next.js Frontend
│   └── package.json               # Dependencias Node
└── docs/
    └── INFORME_TECNICO_CONSOLIDADO.md  # Este informe
```

### Instrucciones de Instalación

1. **Base de Datos (Supabase):**
   ```bash
   # Ejecutar scripts en orden
   psql -h [host] -U [user] -d [database] -f database/01_ddl_tablas.sql
   psql -h [host] -U [user] -d [database] -f database/02_dcl_roles_permisos.sql
   ```

2. **Backend (FastAPI):**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env  # Configurar variables
   python main.py
   ```

3. **Batch Worker:**
   ```bash
   cd batch-worker
   pip install -r requirements.txt
   cp .env.example .env  # Configurar variables
   python main.py
   ```

4. **Frontend (Next.js):**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Redis:**
   ```bash
   redis-server
   # Verificar con: redis-cli ping
   ```

---

## Conclusiones

Este proyecto implementa una arquitectura completa de sistema de tickets con:

✅ **Diseño físico optimizado** con índices compuestos  
✅ **Seguridad basada en roles** con permisos granulares  
✅ **Control de concurrencia** con transacciones y bloqueos  
✅ **Caché y colas Redis** para reducir carga en BD  
✅ **Estrategia de backup** con RPO < 15 minutos  
✅ **Métricas de monitoreo** y acciones de tuning  

La arquitectura es escalable, segura y preparada para producción.

---

**Fecha de Elaboración:** 2024  
**Autor:** Sistema de Tickets de Soporte  
**Versión:** 1.0.0

