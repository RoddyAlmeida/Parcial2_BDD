import { useState, useEffect } from 'react'
import axios from 'axios'
import Head from 'next/head'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [tickets, setTickets] = useState([])
  const [usuarios, setUsuarios] = useState([])
  const [loading, setLoading] = useState(false)
  const [ticketSeleccionado, setTicketSeleccionado] = useState(null)
  const [interacciones, setInteracciones] = useState([])
  const [mostrarFormulario, setMostrarFormulario] = useState(false)
  const [filtroEstado, setFiltroEstado] = useState('todos')
  const [nuevoTicket, setNuevoTicket] = useState({
    usuario_id: '',
    titulo: '',
    descripcion: '',
    prioridad: 'media'
  })

  useEffect(() => {
    cargarTickets()
    cargarUsuarios()
  }, [])

  const cargarTickets = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`${API_URL}/tickets`)
      setTickets(response.data)
    } catch (error) {
      console.error('Error cargando tickets:', error)
    } finally {
      setLoading(false)
    }
  }

  const cargarUsuarios = async () => {
    try {
      const response = await axios.get(`${API_URL}/usuarios`)
      setUsuarios(response.data)
    } catch (error) {
      console.error('Error cargando usuarios:', error)
    }
  }

  const cargarInteracciones = async (ticketId) => {
    try {
      const response = await axios.get(`${API_URL}/tickets/${ticketId}/interacciones`)
      setInteracciones(response.data)
    } catch (error) {
      console.error('Error cargando interacciones:', error)
    }
  }

  const crearTicket = async (e) => {
    e.preventDefault()
    try {
      await axios.post(`${API_URL}/tickets`, nuevoTicket)
      setNuevoTicket({ usuario_id: '', titulo: '', descripcion: '', prioridad: 'media' })
      setMostrarFormulario(false)
      cargarTickets()
    } catch (error) {
      console.error('Error creando ticket:', error)
      alert('Error al crear ticket: ' + (error.response?.data?.detail || error.message))
    }
  }

  const actualizarEstado = async (ticketId, nuevoEstado, usuarioId) => {
    try {
      await axios.patch(`${API_URL}/tickets/${ticketId}/estado?nuevo_estado=${nuevoEstado}&usuario_id=${usuarioId}`)
      cargarTickets()
      if (ticketSeleccionado?.id === ticketId) {
        const updated = tickets.find(t => t.id === ticketId)
        if (updated) {
          setTicketSeleccionado({ ...updated, estado: nuevoEstado })
          cargarInteracciones(ticketId)
        }
      }
    } catch (error) {
      console.error('Error actualizando estado:', error)
      alert('Error al actualizar estado: ' + (error.response?.data?.detail || error.message))
    }
  }

  const verDetalles = async (ticket) => {
    setTicketSeleccionado(ticket)
    await cargarInteracciones(ticket.id)
  }

  const getEstadoColor = (estado) => {
    const colores = {
      'abierto': '#3b82f6',
      'en_proceso': '#f59e0b',
      'resuelto': '#10b981',
      'cerrado': '#6b7280'
    }
    return colores[estado] || '#6b7280'
  }

  const getPrioridadColor = (prioridad) => {
    const colores = {
      'baja': '#6b7280',
      'media': '#3b82f6',
      'alta': '#f59e0b',
      'critica': '#ef4444'
    }
    return colores[prioridad] || '#6b7280'
  }

  const formatearFecha = (fecha) => {
    if (!fecha) return 'N/A'
    return new Date(fecha).toLocaleString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const ticketsFiltrados = filtroEstado === 'todos' 
    ? tickets 
    : tickets.filter(t => t.estado === filtroEstado)

  return (
    <>
      <Head>
        <title>Sistema de Tickets de Soporte</title>
        <meta name="description" content="Gestión de tickets con FastAPI, Next.js, Supabase y Redis" />
      </Head>
      
      <div className="container">
        <header className="header">
          <div className="header-content">
            <div>
              <h1 className="title">Sistema de Tickets</h1>
              <p className="subtitle">Gestión de soporte técnico</p>
            </div>
            <div className="stats">
              <div className="stat-item">
                <span className="stat-number">{tickets.length}</span>
                <span className="stat-label">Total</span>
              </div>
              <div className="stat-item">
                <span className="stat-number">{tickets.filter(t => t.estado === 'abierto').length}</span>
                <span className="stat-label">Abiertos</span>
              </div>
            </div>
          </div>
        </header>

        <div className="main-layout">
          <div className="main-panel">
            <div className="panel-header">
              <div className="filters">
                <button 
                  className={`filter-btn ${filtroEstado === 'todos' ? 'active' : ''}`}
                  onClick={() => setFiltroEstado('todos')}
                >
                  Todos
                </button>
                <button 
                  className={`filter-btn ${filtroEstado === 'abierto' ? 'active' : ''}`}
                  onClick={() => setFiltroEstado('abierto')}
                >
                  Abiertos
                </button>
                <button 
                  className={`filter-btn ${filtroEstado === 'en_proceso' ? 'active' : ''}`}
                  onClick={() => setFiltroEstado('en_proceso')}
                >
                  En Proceso
                </button>
                <button 
                  className={`filter-btn ${filtroEstado === 'resuelto' ? 'active' : ''}`}
                  onClick={() => setFiltroEstado('resuelto')}
                >
                  Resueltos
                </button>
              </div>
              <button
                className="btn-primary"
                onClick={() => setMostrarFormulario(!mostrarFormulario)}
              >
                {mostrarFormulario ? '✕ Cancelar' : '+ Nuevo Ticket'}
              </button>
            </div>

            {mostrarFormulario && (
              <div className="card form-card fade-in">
                <h3 className="form-title">Crear Nuevo Ticket</h3>
                <form onSubmit={crearTicket} className="form">
                  <div className="form-group">
                    <label>Usuario</label>
                    <select
                      value={nuevoTicket.usuario_id}
                      onChange={(e) => setNuevoTicket({ ...nuevoTicket, usuario_id: e.target.value })}
                      required
                      className="form-input"
                    >
                      <option value="">Seleccione un usuario</option>
                      {usuarios.map(usuario => (
                        <option key={usuario.id} value={usuario.id}>
                          {usuario.nombre} ({usuario.email})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Título</label>
                    <input
                      type="text"
                      placeholder="Título del ticket"
                      value={nuevoTicket.titulo}
                      onChange={(e) => setNuevoTicket({ ...nuevoTicket, titulo: e.target.value })}
                      required
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>Descripción</label>
                    <textarea
                      placeholder="Describe el problema o solicitud..."
                      value={nuevoTicket.descripcion}
                      onChange={(e) => setNuevoTicket({ ...nuevoTicket, descripcion: e.target.value })}
                      required
                      rows={4}
                      className="form-input"
                    />
                  </div>
                  <div className="form-group">
                    <label>Prioridad</label>
                    <select
                      value={nuevoTicket.prioridad}
                      onChange={(e) => setNuevoTicket({ ...nuevoTicket, prioridad: e.target.value })}
                      className="form-input"
                    >
                      <option value="baja">🟢 Baja</option>
                      <option value="media">🔵 Media</option>
                      <option value="alta">🟠 Alta</option>
                      <option value="critica">🔴 Crítica</option>
                    </select>
                  </div>
                  <button type="submit" className="btn-success">
                    Crear Ticket
                  </button>
                </form>
              </div>
            )}

            {loading ? (
              <div className="loading">
                <div className="spinner"></div>
                <p>Cargando tickets...</p>
              </div>
            ) : ticketsFiltrados.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">📋</div>
                <p>No hay tickets {filtroEstado !== 'todos' ? `con estado "${filtroEstado}"` : ''}</p>
                {filtroEstado === 'todos' && (
                  <button className="btn-primary" onClick={() => setMostrarFormulario(true)}>
                    Crear primer ticket
                  </button>
                )}
              </div>
            ) : (
              <div className="tickets-list">
                {ticketsFiltrados.map(ticket => (
                  <div
                    key={ticket.id}
                    onClick={() => verDetalles(ticket)}
                    className={`ticket-card ${ticketSeleccionado?.id === ticket.id ? 'selected' : ''}`}
                    style={{ borderLeftColor: getEstadoColor(ticket.estado) }}
                  >
                    <div className="ticket-header">
                      <h3 className="ticket-title">{ticket.titulo}</h3>
                      <span 
                        className="badge-prioridad"
                        style={{
                          backgroundColor: getPrioridadColor(ticket.prioridad) + '20',
                          color: getPrioridadColor(ticket.prioridad)
                        }}
                      >
                        {ticket.prioridad.toUpperCase()}
                      </span>
                    </div>
                    <p className="ticket-description">
                      {ticket.descripcion.substring(0, 120)}{ticket.descripcion.length > 120 ? '...' : ''}
                    </p>
                    <div className="ticket-footer">
                      <span 
                        className="badge-estado"
                        style={{
                          backgroundColor: getEstadoColor(ticket.estado) + '20',
                          color: getEstadoColor(ticket.estado)
                        }}
                      >
                        {ticket.estado.replace('_', ' ')}
                      </span>
                      <span className="ticket-date">{formatearFecha(ticket.fecha_creacion)}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {ticketSeleccionado && (
            <div className="details-panel slide-in">
              <div className="details-header">
                <h2>Detalles del Ticket</h2>
                <button
                  className="close-btn"
                  onClick={() => setTicketSeleccionado(null)}
                >
                  ✕
                </button>
              </div>

              <div className="details-content">
                <div className="detail-section">
                  <h3>{ticketSeleccionado.titulo}</h3>
                  <p className="detail-description">{ticketSeleccionado.descripcion}</p>
                  
                  <div className="detail-grid">
                    <div className="detail-item">
                      <span className="detail-label">Estado</span>
                      <span 
                        className="badge-estado-large"
                        style={{
                          backgroundColor: getEstadoColor(ticketSeleccionado.estado) + '20',
                          color: getEstadoColor(ticketSeleccionado.estado)
                        }}
                      >
                        {ticketSeleccionado.estado.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="detail-item">
                      <span className="detail-label">Prioridad</span>
                      <span 
                        className="badge-prioridad-large"
                        style={{
                          backgroundColor: getPrioridadColor(ticketSeleccionado.prioridad) + '20',
                          color: getPrioridadColor(ticketSeleccionado.prioridad)
                        }}
                      >
                        {ticketSeleccionado.prioridad}
                      </span>
                    </div>
                  </div>

                  <div className="detail-meta">
                    <div>
                      <strong>Creado:</strong> {formatearFecha(ticketSeleccionado.fecha_creacion)}
                    </div>
                    <div>
                      <strong>Actualizado:</strong> {formatearFecha(ticketSeleccionado.fecha_actualizacion)}
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h4>Cambiar Estado</h4>
                  <div className="status-buttons">
                    {['abierto', 'en_proceso', 'resuelto', 'cerrado'].map(estado => (
                      <button
                        key={estado}
                        onClick={() => {
                          const usuarioId = usuarios[0]?.id || ''
                          if (usuarioId) {
                            actualizarEstado(ticketSeleccionado.id, estado, usuarioId)
                          } else {
                            alert('No hay usuarios disponibles. Crea un usuario primero.')
                          }
                        }}
                        disabled={ticketSeleccionado.estado === estado}
                        className={`status-btn ${ticketSeleccionado.estado === estado ? 'active' : ''}`}
                        style={{
                          backgroundColor: ticketSeleccionado.estado === estado 
                            ? getEstadoColor(estado) 
                            : getEstadoColor(estado) + '20',
                          color: ticketSeleccionado.estado === estado ? 'white' : getEstadoColor(estado)
                        }}
                      >
                        {estado.replace('_', ' ')}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="detail-section">
                  <h4>Interacciones ({interacciones.length})</h4>
                  {interacciones.length === 0 ? (
                    <p className="empty-text">No hay interacciones aún.</p>
                  ) : (
                    <div className="interacciones-list">
                      {interacciones.map(interaccion => (
                        <div key={interaccion.id} className="interaccion-item">
                          <div className="interaccion-header">
                            <span className="interaccion-type">{interaccion.tipo.replace('_', ' ')}</span>
                            <span className="interaccion-date">{formatearFecha(interaccion.fecha_creacion)}</span>
                          </div>
                          <p className="interaccion-content">{interaccion.contenido}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .container {
          min-height: 100vh;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 2rem;
        }

        .header {
          background: white;
          border-radius: 1rem;
          padding: 2rem;
          margin-bottom: 2rem;
          box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }

        .header-content {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .title {
          font-size: 2rem;
          font-weight: 700;
          color: #1f2937;
          margin: 0;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .subtitle {
          color: #6b7280;
          margin: 0.5rem 0 0 0;
          font-size: 0.9rem;
        }

        .stats {
          display: flex;
          gap: 2rem;
        }

        .stat-item {
          text-align: center;
        }

        .stat-number {
          display: block;
          font-size: 2rem;
          font-weight: 700;
          color: #667eea;
        }

        .stat-label {
          display: block;
          font-size: 0.875rem;
          color: #6b7280;
          margin-top: 0.25rem;
        }

        .main-layout {
          display: grid;
          grid-template-columns: ${ticketSeleccionado ? '1fr 1fr' : '1fr'};
          gap: 2rem;
        }

        .main-panel {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .filters {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .filter-btn {
          padding: 0.5rem 1rem;
          border: 2px solid #e5e7eb;
          background: white;
          border-radius: 0.5rem;
          cursor: pointer;
          font-weight: 500;
          transition: all 0.2s;
          color: #6b7280;
        }

        .filter-btn:hover {
          border-color: #667eea;
          color: #667eea;
        }

        .filter-btn.active {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }

        .btn-primary {
          padding: 0.75rem 1.5rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          border-radius: 0.5rem;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
          box-shadow: 0 4px 6px rgba(102, 126, 234, 0.3);
        }

        .btn-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
        }

        .btn-success {
          padding: 0.75rem 1.5rem;
          background: #10b981;
          color: white;
          border: none;
          border-radius: 0.5rem;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
          width: 100%;
        }

        .btn-success:hover {
          background: #059669;
          transform: translateY(-2px);
        }

        .card {
          background: white;
          border-radius: 1rem;
          padding: 1.5rem;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .form-card {
          border: 2px solid #e5e7eb;
        }

        .form-title {
          margin: 0 0 1.5rem 0;
          color: #1f2937;
          font-size: 1.5rem;
        }

        .form {
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          font-weight: 600;
          color: #374151;
          font-size: 0.875rem;
        }

        .form-input {
          padding: 0.75rem;
          border: 2px solid #e5e7eb;
          border-radius: 0.5rem;
          font-size: 1rem;
          transition: all 0.2s;
          font-family: inherit;
        }

        .form-input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .tickets-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .ticket-card {
          background: white;
          border-radius: 1rem;
          padding: 1.5rem;
          cursor: pointer;
          transition: all 0.3s;
          border-left: 4px solid;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .ticket-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        }

        .ticket-card.selected {
          border: 2px solid #667eea;
          box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }

        .ticket-header {
          display: flex;
          justify-content: space-between;
          align-items: start;
          margin-bottom: 0.75rem;
        }

        .ticket-title {
          margin: 0;
          color: #1f2937;
          font-size: 1.25rem;
          font-weight: 600;
        }

        .badge-prioridad, .badge-estado {
          padding: 0.25rem 0.75rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        .ticket-description {
          color: #6b7280;
          margin: 0.75rem 0;
          line-height: 1.6;
        }

        .ticket-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-top: 1rem;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .ticket-date {
          font-size: 0.875rem;
          color: #9ca3af;
        }

        .details-panel {
          background: white;
          border-radius: 1rem;
          padding: 2rem;
          box-shadow: 0 10px 25px rgba(0,0,0,0.1);
          position: sticky;
          top: 2rem;
          max-height: calc(100vh - 4rem);
          overflow-y: auto;
        }

        .details-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2rem;
          padding-bottom: 1rem;
          border-bottom: 2px solid #e5e7eb;
        }

        .details-header h2 {
          margin: 0;
          color: #1f2937;
          font-size: 1.5rem;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 1.5rem;
          cursor: pointer;
          color: #6b7280;
          padding: 0.5rem;
          border-radius: 0.5rem;
          transition: all 0.2s;
        }

        .close-btn:hover {
          background: #f3f4f6;
          color: #1f2937;
        }

        .details-content {
          display: flex;
          flex-direction: column;
          gap: 2rem;
        }

        .detail-section h3 {
          margin: 0 0 1rem 0;
          color: #1f2937;
          font-size: 1.25rem;
        }

        .detail-section h4 {
          margin: 0 0 1rem 0;
          color: #374151;
          font-size: 1rem;
        }

        .detail-description {
          color: #6b7280;
          line-height: 1.6;
          margin-bottom: 1.5rem;
        }

        .detail-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .detail-item {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .detail-label {
          font-size: 0.875rem;
          color: #6b7280;
          font-weight: 500;
        }

        .badge-estado-large, .badge-prioridad-large {
          padding: 0.5rem 1rem;
          border-radius: 0.5rem;
          font-weight: 600;
          display: inline-block;
        }

        .detail-meta {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: #6b7280;
          padding-top: 1rem;
          border-top: 1px solid #e5e7eb;
        }

        .status-buttons {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .status-btn {
          padding: 0.75rem 1.25rem;
          border: none;
          border-radius: 0.5rem;
          cursor: pointer;
          font-weight: 600;
          transition: all 0.2s;
          font-size: 0.875rem;
        }

        .status-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .status-btn:disabled {
          cursor: not-allowed;
          opacity: 0.7;
        }

        .interacciones-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          max-height: 400px;
          overflow-y: auto;
          padding-right: 0.5rem;
        }

        .interaccion-item {
          background: #f9fafb;
          padding: 1rem;
          border-radius: 0.5rem;
          border: 1px solid #e5e7eb;
        }

        .interaccion-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 0.5rem;
        }

        .interaccion-type {
          font-weight: 600;
          color: #374151;
          font-size: 0.875rem;
        }

        .interaccion-date {
          font-size: 0.75rem;
          color: #9ca3af;
        }

        .interaccion-content {
          margin: 0;
          color: #6b7280;
          font-size: 0.875rem;
          line-height: 1.6;
        }

        .loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 4rem;
          color: white;
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(255,255,255,0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin-bottom: 1rem;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        .empty-state {
          text-align: center;
          padding: 4rem 2rem;
          background: white;
          border-radius: 1rem;
          color: #6b7280;
        }

        .empty-icon {
          font-size: 4rem;
          margin-bottom: 1rem;
        }

        .empty-text {
          color: #9ca3af;
          font-style: italic;
        }

        .fade-in {
          animation: fadeIn 0.3s ease-out;
        }

        .slide-in {
          animation: slideIn 0.3s ease-out;
        }

        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        @media (max-width: 1024px) {
          .main-layout {
            grid-template-columns: 1fr;
          }
          
          .details-panel {
            position: relative;
            top: 0;
            max-height: none;
          }
        }
      `}</style>
    </>
  )
}
