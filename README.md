# Práctica de Implementación y Administración de la Arquitectura de Datos

## Arquitectura del Sistema

Este proyecto implementa un sistema de tickets de soporte con la siguiente arquitectura:

- **Frontend**: Next.js
- **API Server**: FastAPI
- **Batch Worker**: Proceso independiente para procesamiento asíncrono
- **Base de Datos**: PostgreSQL
- **Caché y Colas**: Redis

## Estructura del Proyecto

```
Actividad_BDD/
├── backend/              # FastAPI Server
├── frontend/             # Next.js Application
├── batch-worker/         # Batch Worker Process
├── database/             # Scripts SQL
├── redis/                # Scripts y configuración Redis
└── docs/                 # Documentación e Informe Técnico
```

## Requisitos

- Python 3.9+
- Node.js 18+
- Redis (local o servicio en la nube)
- PostgreSQL (local o servicio en la nube)

## Instalación

Ver instrucciones detalladas en cada directorio.

