import { BrowserRouter, Routes, Route, Link, NavLink } from 'react-router-dom'
import { useState, useEffect } from 'react'
import api, { endpoints } from './api'
import './App.css'

// Components
function Navigation() {
  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/">🏥 HospiPlan2</Link>
      </div>
      <div className="nav-links">
        <NavLink to="/staff" className={({ isActive }) => isActive ? 'active' : ''}>
          👥 Personnel
        </NavLink>
        <NavLink to="/shifts" className={({ isActive }) => isActive ? 'active' : ''}>
          📅 Postes
        </NavLink>
        <NavLink to="/planning" className={({ isActive }) => isActive ? 'active' : ''}>
          📋 Planning
        </NavLink>
        <NavLink to="/optimization" className={({ isActive }) => isActive ? 'active' : ''}>
          🤖 Génération
        </NavLink>
        <NavLink to="/config" className={({ isActive }) => isActive ? 'active' : ''}>
          ⚙️ Config
        </NavLink>
      </div>
    </nav>
  )
}

function Dashboard() {
  const [stats, setStats] = useState({
    staff: 0,
    shifts: 0,
    assignments: 0,
    absences: 0
  })

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [staffRes, shiftsRes, assignmentsRes, absencesRes] = await Promise.all([
          api.get(endpoints.staff),
          api.get(endpoints.shifts),
          api.get(endpoints.assignments),
          api.get(endpoints.absences)
        ])
        setStats({
          staff: staffRes.data.count || 0,
          shifts: shiftsRes.data.count || 0,
          assignments: assignmentsRes.data.count || 0,
          absences: absencesRes.data.count || 0
        })
      } catch (error) {
        console.error('Error fetching stats:', error)
      }
    }
    fetchStats()
  }, [])

  return (
    <div className="dashboard">
      <h1>🏥 HospiPlan2 - Tableau de bord</h1>
      <div className="stats-grid">
        <div className="stat-card">
          <span className="stat-icon">👥</span>
          <span className="stat-value">{stats.staff}</span>
          <span className="stat-label">Personnels</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📅</span>
          <span className="stat-value">{stats.shifts}</span>
          <span className="stat-label">Postes</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">📋</span>
          <span className="stat-value">{stats.assignments}</span>
          <span className="stat-label">Affectations</span>
        </div>
        <div className="stat-card">
          <span className="stat-icon">⚠️</span>
          <span className="stat-value">{stats.absences}</span>
          <span className="stat-label">Absences</span>
        </div>
      </div>
      <div className="quick-actions">
        <h2>Actions rapides</h2>
        <div className="action-buttons">
          <Link to="/staff" className="action-btn">
            ➕ Ajouter du personnel
          </Link>
          <Link to="/shifts" className="action-btn">
            ➕ Créer un poste
          </Link>
          <Link to="/optimization" className="action-btn action-btn-primary">
            🤖 Générer un planning
          </Link>
        </div>
      </div>
    </div>
  )
}

function StaffList() {
  const [staff, setStaff] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStaff = async () => {
      try {
        const response = await api.get(endpoints.staff)
        setStaff(response.data.results || response.data)
      } catch (error) {
        console.error('Error fetching staff:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchStaff()
  }, [])

  if (loading) return <div className="loading">Chargement...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h1>👥 Gestion du Personnel</h1>
        <button className="btn btn-primary">➕ Nouveau</button>
      </div>
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Nom</th>
              <th>Prénom</th>
              <th>Email</th>
              <th>Rôles</th>
              <th>Statut</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {staff.map(person => (
              <tr key={person.id}>
                <td>{person.last_name}</td>
                <td>{person.first_name}</td>
                <td>{person.email}</td>
                <td>{person.roles?.join(', ') || '-'}</td>
                <td>
                  <span className={`badge ${person.is_active ? 'badge-success' : 'badge-danger'}`}>
                    {person.is_active ? 'Actif' : 'Inactif'}
                  </span>
                </td>
                <td>
                  <button className="btn btn-sm">👁️</button>
                  <button className="btn btn-sm">✏️</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function ShiftsList() {
  const [shifts, setShifts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchShifts = async () => {
      try {
        const response = await api.get(endpoints.shifts)
        setShifts(response.data.results || response.data)
      } catch (error) {
        console.error('Error fetching shifts:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchShifts()
  }, [])

  if (loading) return <div className="loading">Chargement...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h1>📅 Gestion des Postes</h1>
        <button className="btn btn-primary">➕ Nouveau poste</button>
      </div>
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Service</th>
              <th>Unité</th>
              <th>Type</th>
              <th>Début</th>
              <th>Fin</th>
              <th>Effectif</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {shifts.map(shift => (
              <tr key={shift.id}>
                <td>{shift.service_name || '-'}</td>
                <td>{shift.care_unit_name || '-'}</td>
                <td>{shift.shift_type_name || '-'}</td>
                <td>{new Date(shift.start_datetime).toLocaleString('fr-FR')}</td>
                <td>{new Date(shift.end_datetime).toLocaleString('fr-FR')}</td>
                <td>{shift.assigned_count || 0}/{shift.max_staff}</td>
                <td>
                  <button className="btn btn-sm">👁️</button>
                  <button className="btn btn-sm">✏️</button>
                  <button className="btn btn-sm btn-danger">🗑️</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function PlanningView() {
  const [assignments, setAssignments] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchAssignments = async () => {
      try {
        const response = await api.get(endpoints.assignments)
        setAssignments(response.data.results || response.data)
      } catch (error) {
        console.error('Error fetching assignments:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchAssignments()
  }, [])

  if (loading) return <div className="loading">Chargement...</div>

  return (
    <div className="page">
      <div className="page-header">
        <h1>📋 Planning des Affectations</h1>
        <button className="btn btn-primary">➕ Nouvelle affectation</button>
      </div>
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th>Personnel</th>
              <th>Poste</th>
              <th>Service</th>
              <th>Date</th>
              <th>Statut</th>
              <th>Source</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {assignments.map(assignment => (
              <tr key={assignment.id}>
                <td>{assignment.staff_name || '-'}</td>
                <td>{assignment.shift_label || '-'}</td>
                <td>{assignment.service_name || '-'}</td>
                <td>{assignment.start_datetime ? new Date(assignment.start_datetime).toLocaleString('fr-FR') : '-'}</td>
                <td>
                  <span className={`badge ${
                    assignment.status === 'confirmed' ? 'badge-success' :
                    assignment.status === 'pending' ? 'badge-warning' : 'badge-danger'
                  }`}>
                    {assignment.status_display || assignment.status}
                  </span>
                </td>
                <td>
                  <span className="badge badge-info">
                    {assignment.source_display || assignment.source}
                  </span>
                </td>
                <td>
                  <button className="btn btn-sm">👁️</button>
                  <button className="btn btn-sm btn-danger">🗑️</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function OptimizationView() {
  const [config, setConfig] = useState({
    start_date: '',
    end_date: '',
    service_id: '',
  })
  const [generating, setGenerating] = useState(false)
  const [result, setResult] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setGenerating(true)
    try {
      const response = await api.post(endpoints.generate, config)
      setResult(response.data)
    } catch (error) {
      console.error('Error generating planning:', error)
      setResult({ error: error.message })
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>🤖 Génération Automatique</h1>
      </div>
      <div className="card">
        <h2>Paramètres de génération</h2>
        <form onSubmit={handleSubmit} className="form">
          <div className="form-group">
            <label>Date de début</label>
            <input
              type="date"
              value={config.start_date}
              onChange={(e) => setConfig({...config, start_date: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Date de fin</label>
            <input
              type="date"
              value={config.end_date}
              onChange={(e) => setConfig({...config, end_date: e.target.value})}
              required
            />
          </div>
          <div className="form-group">
            <label>Service (optionnel)</label>
            <input
              type="text"
              value={config.service_id}
              onChange={(e) => setConfig({...config, service_id: e.target.value})}
              placeholder="Laisser vide pour tous les services"
            />
          </div>
          <button type="submit" className="btn btn-primary btn-lg" disabled={generating}>
            {generating ? '⏳ Génération en cours...' : '🚀 Lancer la génération'}
          </button>
        </form>
      </div>
      {result && (
        <div className="card">
          <h2>Résultat</h2>
          {result.error ? (
            <div className="alert alert-danger">{result.error}</div>
          ) : (
            <div className="alert alert-success">
              <p>✅ Génération lancée avec succès !</p>
              <p>ID de la génération : {result.run_id}</p>
              <p>{result.message}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function ConfigView() {
  return (
    <div className="page">
      <div className="page-header">
        <h1>⚙️ Configuration</h1>
      </div>
      <div className="config-grid">
        <div className="card">
          <h3>🏢 Services</h3>
          <p>Gérez les services hospitaliers</p>
          <button className="btn">Accéder</button>
        </div>
        <div className="card">
          <h3>🏥 Unités de soin</h3>
          <p>Gérez les unités de soin</p>
          <button className="btn">Accéder</button>
        </div>
        <div className="card">
          <h3>⏰ Types de poste</h3>
          <p>Configurez les types de poste (Jour, Nuit, etc.)</p>
          <button className="btn">Accéder</button>
        </div>
        <div className="card">
          <h3>📋 Types d'absence</h3>
          <p>Configurez les types d'absence</p>
          <button className="btn">Accéder</button>
        </div>
        <div className="card">
          <h3>🎯 Règles métier</h3>
          <p>Configurez les règles de planification</p>
          <button className="btn">Accéder</button>
        </div>
        <div className="card">
          <h3>🤖 Config optimisation</h3>
          <p>Paramètres de génération automatique</p>
          <button className="btn">Accéder</button>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/staff" element={<StaffList />} />
            <Route path="/shifts" element={<ShiftsList />} />
            <Route path="/planning" element={<PlanningView />} />
            <Route path="/optimization" element={<OptimizationView />} />
            <Route path="/config" element={<ConfigView />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App