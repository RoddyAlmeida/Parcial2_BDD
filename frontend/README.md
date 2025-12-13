# Frontend - Next.js

Frontend del Sistema de Tickets de Soporte construido con Next.js.

## Características

- ✅ Lista de tickets con filtros visuales
- ✅ Crear nuevos tickets
- ✅ Ver detalles de tickets
- ✅ Actualizar estado de tickets
- ✅ Ver interacciones/comentarios
- ✅ UI moderna y responsive
- ✅ Integración con API FastAPI

## Instalación

```bash
cd frontend
npm install
```

## Configuración

Crea un archivo `.env.local` (opcional):

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Por defecto, el frontend se conecta a `http://localhost:8000`.

## Ejecución

### Desarrollo

```bash
npm run dev
```

El frontend estará disponible en: `http://localhost:3000`

### Producción

```bash
npm run build
npm start
```

## Estructura

```
frontend/
├── pages/
│   └── index.js          # Página principal
├── package.json          # Dependencias
├── next.config.js        # Configuración Next.js
└── README.md            # Este archivo
```

## Uso

1. **Ver Tickets**: La lista de tickets se carga automáticamente al iniciar
2. **Crear Ticket**: Haz clic en "+ Nuevo Ticket" y completa el formulario
3. **Ver Detalles**: Haz clic en cualquier ticket para ver sus detalles
4. **Cambiar Estado**: En el panel de detalles, usa los botones para cambiar el estado
5. **Ver Interacciones**: Las interacciones se muestran automáticamente en el panel de detalles

## Requisitos

- Node.js 18+
- Backend FastAPI corriendo en `http://localhost:8000`
- Base de datos con usuarios y tickets creados

