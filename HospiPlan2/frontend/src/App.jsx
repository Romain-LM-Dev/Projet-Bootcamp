import { BrowserRouter, Link, NavLink, Route, Routes } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import api, { endpoints } from './api'
import { useAuth } from './AuthContext'
import './App.css'

const SHIFT_TYPE_COLORS = {
  Jour: '#2563eb',
  Soir: '#f59e0b',
  Nuit: '#7c3aed',
  '12h Jour': '#0f766e',
  '12h Nuit': '#9333ea',
}

const STATUS_VARIANTS = {
  completed: 'success',
  success: 'success',
  running: 'warning',
  pending: 'warning',
  in_progress: 'warning',
  failed: 'danger',
  error: 'danger',
  default: 'neutral',
}

function normalizeListResponse(data) {
  if (Array.isArray(data)) return data
  if (Array.isArray(data?.results)) return data.results
  return []
}

function extractCount(data) {
  if (typeof data?.count === 'number') return data.count
  return normalizeListResponse(data).length
}

function toDateKey(value) {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function getWeekStartFromDate(value = new Date()) {
  const date = value instanceof Date ? new Date(value) : new Date(value)
  const day = date.getDay()
  const diff = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + diff)
  return toDateKey(date)
}

function getWeekDays(weekStart) {
  const start = new Date(weekStart)
  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(start)
    date.setDate(start.getDate() + index)
    return date
  })
}

function groupAssignmentsByShift(assignments) {
  return assignments.reduce((acc, assignment) => {
    const shiftId = typeof assignment.shift === 'object' ? assignment.shift?.id : assignment.shift
    if (!shiftId) return acc
    if (!acc[shiftId]) acc[shiftId] = []
    acc[shiftId].push(assignment)
    return acc
  }, {})
}

function filterShifts({ shifts, serviceId, careUnitId, weekStart, weekEnd }) {
  return shifts.filter((shift) => {
    const shiftDate = toDateKey(shift.start_datetime)
    const shiftServiceId = String(shift.service ?? shift.service_id ?? shift.care_unit_service ?? '')
    const shiftCareUnitId = String(shift.care_unit ?? shift.care_unit_id ?? '')
    const matchService = !serviceId || shiftServiceId === String(serviceId)
    const matchCareUnit = !careUnitId || shiftCareUnitId === String(careUnitId)
    const matchWeek = shiftDate >= weekStart && shiftDate <= weekEnd
    return matchService && matchCareUnit && matchWeek
  })
}

function formatDate(date, options = {}) {
  return new Intl.DateTimeFormat('fr-FR', options).format(date)
}

function formatDateTime(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString('fr-FR')
}

function getStatusVariant(status) {
  return STATUS_VARIANTS[status] || STATUS_VARIANTS.default
}

function getShiftTypeColor(name) {
  return SHIFT_TYPE_COLORS[name] || '#64748b'
}

function AppShell({ children }) {
  const { user, isAuthenticated, isAdmin, logout, isLoading } = useAuth()

  const getInitials = (name) => {
    if (!name) return 'U'
    const parts = name.split(' ')
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase()
    }
    return name.substring(0, 2).toUpperCase()
  }

  const userDisplay = isAuthenticated ? user : null
  const userInitials = userDisplay
    ? getInitials(userDisplay.first_name ? `${userDisplay.first_name} ${userDisplay.last_name}` : userDisplay.username)
    : 'U'

  if (isLoading) {
    return (
      <div className="app-shell">
        <aside className="sidebar">
          <div className="brand-card">
            <div className="brand-mark">HP2</div>
            <div>
              <p className="eyebrow">Plateforme hospitalière</p>
              <h1>HospiPlan2</h1>
            </div>
          </div>
        </aside>
        <div className="app-body">
          <main className="page-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <div style={{ textAlign: 'center' }}>
              <div className="spinner" style={{ margin: '0 auto 16px' }}></div>
              <p>Chargement...</p>
            </div>
          </main>
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <Link to="/" className="brand-card">
          <div className="brand-mark">HP2</div>
          <div>
            <p className="eyebrow">Plateforme hospitalière</p>
            <h1>HospiPlan2</h1>
          </div>
        </Link>

        <nav className="sidebar-nav">
          <NavLink to="/" end className="nav-item">
            <span>Vue d'ensemble</span>
          </NavLink>
          <NavLink to="/planning" className="nav-item">
            <span>Planning</span>
          </NavLink>
          <NavLink to="/staff" className="nav-item">
            <span>Personnel</span>
          </NavLink>
          <NavLink to="/shifts" className="nav-item">
            <span>Postes</span>
          </NavLink>
          <NavLink to="/optimization" className="nav-item">
            <span>Génération auto</span>
          </NavLink>
          <NavLink to="/config" className="nav-item">
            <span>Configuration</span>
          </NavLink>
        </nav>

        <div className="sidebar-panel">
          <p className="panel-label">Centre de pilotage</p>
          <strong>Gestion des plannings</strong>
          <span>Organisation des équipes, suivi des postes et accès à l'administration technique.</span>
        </div>
      </aside>

      <div className="app-body">
        <header className="topbar">
          <div>
            <p className="eyebrow">Pilotage hospitalier</p>
            <h2>Organisation des gardes et affectations</h2>
          </div>
          <div className="topbar-user">
            <div className="user-avatar">{userInitials}</div>
            <div>
              {isAuthenticated ? (
                <>
                  <strong>{userDisplay.first_name ? `${userDisplay.first_name} ${userDisplay.last_name}` : userDisplay.username}</strong>
                  <span>{isAdmin ? 'Administrateur' : 'Utilisateur'}</span>
                </>
              ) : (
                <>
                  <strong>Non connecté</strong>
                  <span>Connectez-vous pour accéder à l'administration</span>
                </>
              )}
            </div>
            {isAuthenticated && (
              <button onClick={logout} className="btn btn-secondary btn-sm" style={{ marginLeft: '12px' }}>
                Déconnexion
              </button>
            )}
          </div>
        </header>

        <main className="page-content">{children}</main>
      </div>
    </div>
  )
}

function PageHeader({ title, subtitle, badge, actions }) {
  return (
    <div className="page-header">
      <div>
        <p className="eyebrow">{subtitle}</p>
        <div className="page-title-row">
          <h1>{title}</h1>
          {badge ? <span className="page-badge">{badge}</span> : null}
        </div>
      </div>
      {actions ? <div className="page-actions">{actions}</div> : null}
    </div>
  )
}

function LoadingState({ label = 'Chargement des données...' }) {
  return (
    <div className="state-card">
      <div className="spinner" />
      <p>{label}</p>
    </div>
  )
}

function EmptyState({ title, description }) {
  return (
    <div className="state-card empty">
      <h3>{title}</h3>
      <p>{description}</p>
    </div>
  )
}

function StatusBadge({ children, variant = 'neutral' }) {
  return <span className={`status-badge ${variant}`}>{children}</span>
}

function StatCard({ label, value, hint, tone = 'default' }) {
  return (
    <div className={`stat-card tone-${tone}`}>
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      <span className="stat-hint">{hint}</span>
    </div>
  )
}

function DataTable({ columns, rows, keyField, emptyTitle, emptyDescription }) {
  if (!rows.length) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />
  }

  return (
    <div className="table-card">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[keyField]}>
              {columns.map((column) => (
                <td key={column.key}>{column.render ? column.render(row) : row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function DashboardPage() {
  const [stats, setStats] = useState({ staff: 0, shifts: 0, assignments: 0, absences: 0 })
  const [recentRuns, setRecentRuns] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const [staffRes, shiftsRes, assignmentsRes, absencesRes, runsRes] = await Promise.all([
          api.get(endpoints.staff),
          api.get(endpoints.shifts),
          api.get(endpoints.assignments),
          api.get(endpoints.absences),
          api.get(endpoints.optimizationRuns),
        ])

        setStats({
          staff: extractCount(staffRes.data),
          shifts: extractCount(shiftsRes.data),
          assignments: extractCount(assignmentsRes.data),
          absences: extractCount(absencesRes.data),
        })
        setRecentRuns(normalizeListResponse(runsRes.data).slice(0, 4))
      } catch (error) {
        console.error('Dashboard loading error:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [])

  if (loading) return <LoadingState label="Chargement du tableau de bord..." />

  return (
    <div className="page-stack">
      <PageHeader
        title="Tableau de bord"
        subtitle="Supervision globale"
        badge="Temps réel"
        actions={
          <>
            <Link to="/planning" className="btn btn-secondary">
              Consulter le planning
            </Link>
            <Link to="/optimization" className="btn btn-primary">
              Lancer une génération
            </Link>
          </>
        }
      />

      <section className="stats-grid">
        <StatCard label="Personnel actif" value={stats.staff} hint="Ressources disponibles" tone="blue" />
        <StatCard label="Postes planifiés" value={stats.shifts} hint="Période en base" tone="amber" />
        <StatCard label="Affectations" value={stats.assignments} hint="Assignations enregistrées" tone="green" />
        <StatCard label="Absences" value={stats.absences} hint="Situations à anticiper" tone="purple" />
      </section>

      <section className="dashboard-grid">
        <div className="panel-card hero-card">
          <div>
            <p className="eyebrow">Centre de coordination</p>
            <h3>Un pilotage plus clair des plannings hospitaliers</h3>
            <p>
              Consultez rapidement la couverture, détectez les tensions sur les équipes et lancez une
              génération automatisée depuis une interface structurée et lisible.
            </p>
          </div>
          <div className="hero-actions">
            <Link to="/staff" className="btn btn-secondary">
              Voir le personnel
            </Link>
            <Link to="/shifts" className="btn btn-secondary">
              Voir les postes
            </Link>
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-header">
            <h3>Dernières générations</h3>
            <Link to="/optimization" className="text-link">
              Historique
            </Link>
          </div>

          {recentRuns.length ? (
            <div className="activity-list">
              {recentRuns.map((run) => (
                <div key={run.id} className="activity-item">
                  <div>
                    <strong>{run.name}</strong>
                    <p>
                      {run.created_at ? formatDate(new Date(run.created_at), { dateStyle: 'medium' }) : 'Date inconnue'} ·
                      Couverture {run.coverage_rate ?? 0}%
                    </p>
                  </div>
                  <StatusBadge variant={getStatusVariant(run.status)}>
                    {run.status === 'completed' ? 'Terminé' : run.status}
                  </StatusBadge>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="Aucune génération récente"
              description="Lancez une génération automatique pour alimenter l’activité récente."
            />
          )}
        </div>
      </section>
    </div>
  )
}

function PlanningPage() {
  const [assignments, setAssignments] = useState([])
  const [shifts, setShifts] = useState([])
  const [staff, setStaff] = useState([])
  const [services, setServices] = useState([])
  const [careUnits, setCareUnits] = useState([])
  const [shiftTypes, setShiftTypes] = useState([])
  const [absences, setAbsences] = useState([])
  const [selectedService, setSelectedService] = useState('')
  const [selectedCareUnit, setSelectedCareUnit] = useState('')
  const [weekStart, setWeekStart] = useState(getWeekStartFromDate())
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPlanning = async () => {
      setLoading(true)
      try {
        const currentWeekEnd = toDateKey(getWeekDays(weekStart)[6])
        const [assignmentsRes, shiftsRes, staffRes, servicesRes, careUnitsRes, shiftTypesRes, absencesRes] = await Promise.all([
          api.get(`${endpoints.assignments}?start_date=${weekStart}&end_date=${currentWeekEnd}`),
          api.get(`${endpoints.shifts}?start_date=${weekStart}&end_date=${currentWeekEnd}`),
          api.get(endpoints.staff),
          api.get(endpoints.services),
          api.get(endpoints.careUnits),
          api.get(endpoints.shiftTypes),
          api.get(`${endpoints.absences}?start_date=${weekStart}&end_date=${currentWeekEnd}`),
        ])

        setAssignments(normalizeListResponse(assignmentsRes.data))
        setShifts(normalizeListResponse(shiftsRes.data))
        setStaff(normalizeListResponse(staffRes.data))
        setServices(normalizeListResponse(servicesRes.data))
        setCareUnits(normalizeListResponse(careUnitsRes.data))
        setShiftTypes(normalizeListResponse(shiftTypesRes.data))
        setAbsences(normalizeListResponse(absencesRes.data))
      } catch (error) {
        console.error('Planning loading error:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchPlanning()
  }, [weekStart])

  const weekDays = useMemo(() => getWeekDays(weekStart), [weekStart])
  const weekEnd = useMemo(() => toDateKey(weekDays[6]), [weekDays])
  const assignmentsByShift = useMemo(() => groupAssignmentsByShift(assignments), [assignments])

  // Filter absences for the current week
  const absencesThisWeek = useMemo(() => {
    return absences.filter((absence) => {
      const absenceStart = toDateKey(absence.start_date)
      const absenceEnd = toDateKey(absence.expected_end_date || absence.start_date)
      // Check if absence overlaps with the current week
      return absenceEnd >= weekStart && absenceStart <= weekEnd
    })
  }, [absences, weekStart, weekEnd])

  // Get absences by date
  const absencesByDate = useMemo(() => {
    const byDate = {}
    absencesThisWeek.forEach((absence) => {
      const start = new Date(absence.start_date)
      const end = new Date(absence.expected_end_date || absence.start_date)
      // Mark all days in the absence range
      for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        const dateKey = toDateKey(d)
        if (dateKey >= weekStart && dateKey <= weekEnd) {
          if (!byDate[dateKey]) byDate[dateKey] = []
          byDate[dateKey].push(absence)
        }
      }
    })
    return byDate
  }, [absencesThisWeek, weekStart, weekEnd])

  const availableCareUnits = useMemo(() => {
    return careUnits.filter((unit) => !selectedService || String(unit.service) === String(selectedService))
  }, [careUnits, selectedService])

  const visibleShifts = useMemo(
    () =>
      filterShifts({
        shifts,
        serviceId: selectedService,
        careUnitId: selectedCareUnit,
        weekStart,
        weekEnd,
      }),
    [selectedCareUnit, selectedService, shifts, weekEnd, weekStart]
  )

  const shiftTypesById = useMemo(() => {
    return shiftTypes.reduce((acc, type) => {
      acc[type.id] = type.name
      return acc
    }, {})
  }, [shiftTypes])

  const staffMap = useMemo(() => {
    return staff.reduce((acc, person) => {
      acc[person.id] = `${person.first_name ?? ''} ${person.last_name ?? ''}`.trim()
      return acc
    }, {})
  }, [staff])

  const groupedByCareUnit = useMemo(() => {
    const group = {}
    visibleShifts.forEach((shift) => {
      const careUnitId = shift.care_unit ?? shift.care_unit_id ?? 'unknown'
      const careUnitName =
        shift.care_unit_name ||
        careUnits.find((unit) => unit.id === careUnitId)?.name ||
        'Unité inconnue'

      if (!group[careUnitId]) {
        group[careUnitId] = { id: careUnitId, name: careUnitName, shiftsByDay: {} }
      }

      const key = toDateKey(shift.start_datetime)
      if (!group[careUnitId].shiftsByDay[key]) {
        group[careUnitId].shiftsByDay[key] = []
      }
      group[careUnitId].shiftsByDay[key].push(shift)
    })

    return Object.values(group)
  }, [visibleShifts, careUnits])

  if (loading) return <LoadingState label="Chargement du planning..." />

  return (
    <div className="page-stack">
      <PageHeader
        title="Planning hebdomadaire"
        subtitle="Visualisation opérationnelle"
        badge={`${groupedByCareUnit.length} unité(s) affichée(s)`}
        actions={
          <>
            <input type="date" value={weekStart} onChange={(e) => setWeekStart(getWeekStartFromDate(e.target.value))} className="field-control" />
            <Link to="/optimization" className="btn btn-primary">
              Génération auto
            </Link>
          </>
        }
      />

      <section className="panel-card filters-card">
        <div className="filter-row">
          <select
            value={selectedService}
            onChange={(e) => {
              setSelectedService(e.target.value)
              setSelectedCareUnit('')
            }}
            className="field-control"
          >
            <option value="">Tous les services</option>
            {services.map((service) => (
              <option key={service.id} value={service.id}>
                {service.name}
              </option>
            ))}
          </select>

          <select value={selectedCareUnit} onChange={(e) => setSelectedCareUnit(e.target.value)} className="field-control">
            <option value="">Toutes les unités</option>
            {availableCareUnits.map((careUnit) => (
              <option key={careUnit.id} value={careUnit.id}>
                {careUnit.name}
              </option>
            ))}
          </select>
        </div>
      </section>

      {absencesThisWeek.length > 0 && (
        <section className="panel-card">
          <h3>⚠️ Absences cette semaine ({absencesThisWeek.length})</h3>
          <div className="absences-grid">
            {weekDays.map((day) => {
              const dateKey = toDateKey(day)
              const dayAbsences = absencesByDate[dateKey] || []
              if (dayAbsences.length === 0) return null
              return (
                <div key={dateKey} className="absence-day">
                  <strong>{formatDate(day, { weekday: 'short', day: '2-digit', month: '2-digit' })}</strong>
                  <ul className="absence-list">
                    {dayAbsences.map((absence) => (
                      <li key={absence.id} className="absence-item">
                        <span className="absence-staff">{absence.staff_name}</span>
                        <span className="absence-type" style={{ color: '#dc2626' }}>{absence.absence_type_name}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )
            })}
          </div>
        </section>
      )}

      <section className="planning-board">
        <div className="planning-grid">
          <div className="planning-cell planning-corner">Unité / jour</div>
          {weekDays.map((day) => (
            <div key={toDateKey(day)} className="planning-cell planning-head">
              <strong>{formatDate(day, { weekday: 'long' })}</strong>
              <span>{formatDate(day, { day: '2-digit', month: '2-digit' })}</span>
            </div>
          ))}

          {groupedByCareUnit.length ? (
            groupedByCareUnit.map((careUnit) => (
              <FragmentLike
                keyValue={careUnit.id}
                content={
                  <>
                    <div className="planning-cell planning-label">{careUnit.name}</div>
                    {weekDays.map((day) => {
                      const dateKey = toDateKey(day)
                      const dayShifts = careUnit.shiftsByDay[dateKey] || []

                      return (
                        <div key={`${careUnit.id}-${dateKey}`} className="planning-cell planning-day">
                          {dayShifts.length ? (
                            dayShifts.map((shift) => {
                              const shiftAssignments = assignmentsByShift[shift.id] || []
                              const typeName = shift.shift_type_name || shiftTypesById[shift.shift_type] || 'Poste'
                              return (
                                <article key={shift.id} className="shift-card" style={{ '--shift-accent': getShiftTypeColor(typeName) }}>
                                  <div className="shift-card-top">
                                    <strong>{typeName}</strong>
                                    <span>
                                      {shiftAssignments.length}/{shift.max_staff}
                                    </span>
                                  </div>
                                  <p className="shift-meta">
                                    {formatDateTime(shift.start_datetime).slice(11, 16)} → {formatDateTime(shift.end_datetime).slice(11, 16)}
                                  </p>
                                  <div className="chip-list">
                                    {shiftAssignments.length ? (
                                      shiftAssignments.map((assignment) => (
                                        <span key={assignment.id} className="staff-chip">
                                          {assignment.staff_name || staffMap[assignment.staff] || 'Inconnu'}
                                        </span>
                                      ))
                                    ) : (
                                      <span className="muted-text">Aucune affectation</span>
                                    )}
                                  </div>
                                </article>
                              )
                            })
                          ) : (
                            <span className="muted-text">—</span>
                          )}
                        </div>
                      )
                    })}
                  </>
                }
              />
            ))
          ) : (
            <div className="planning-empty">
              <EmptyState
                title="Aucun poste trouvé"
                description="Ajustez les filtres ou lancez une génération automatique pour remplir cette semaine."
              />
            </div>
          )}
        </div>
      </section>
    </div>
  )
}

function FragmentLike({ content }) {
  return content
}

const EMPTY_FORM = {
  first_name: '', last_name: '', email: '', employee_id: '', phone: '',
  role_id: '', contract_type_id: '', hire_date: toDateKey(new Date()),
}

function StaffPage() {
  const [staff, setStaff] = useState([])
  const [roles, setRoles] = useState([])
  const [contractTypes, setContractTypes] = useState([])
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)

  const fetchStaff = async () => {
    try {
      const [staffRes, rolesRes, ctRes] = await Promise.all([
        api.get(endpoints.staff),
        api.get(endpoints.roles),
        api.get(endpoints.contractTypes),
      ])
      setStaff(normalizeListResponse(staffRes.data))
      setRoles(normalizeListResponse(rolesRes.data))
      setContractTypes(normalizeListResponse(ctRes.data))
    } catch (error) {
      console.error('Staff loading error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchStaff() }, [])

  const openModal = () => { setForm(EMPTY_FORM); setFormError(''); setShowModal(true) }
  const closeModal = () => { setShowModal(false); setFormError('') }

  const handleField = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError('')
    setSaving(true)
    try {
      // 1. Créer l'agent
      const payload = {
        first_name: form.first_name,
        last_name: form.last_name,
        email: form.email,
        is_active: true,
        hire_date: form.hire_date || toDateKey(new Date()),
      }
      if (form.employee_id) payload.employee_id = form.employee_id
      if (form.phone) payload.phone = form.phone

      const res = await api.post(endpoints.staff, payload)
      const newStaffId = res.data.id

      // 2. Associer le rôle
      if (form.role_id && newStaffId) {
        await api.post(endpoints.staffRoles, { staff: newStaffId, role: Number(form.role_id) })
      }

      // 3. Créer le contrat (nécessaire pour la planification automatique)
      if (form.contract_type_id && newStaffId) {
        await api.post(endpoints.contracts, {
          staff: newStaffId,
          contract_type: Number(form.contract_type_id),
          start_date: form.hire_date || toDateKey(new Date()),
          workload_percent: 100,
          is_current: true,
        })
      }

      await fetchStaff()
      closeModal()
    } catch (error) {
      const data = error.response?.data
      if (data?.email) setFormError(`Email : ${data.email[0]}`)
      else if (data?.employee_id) setFormError(`Matricule : ${data.employee_id[0]}`)
      else if (data?.detail) setFormError(data.detail)
      else setFormError("Erreur lors de la création de l'agent.")
    } finally {
      setSaving(false)
    }
  }

  const rows = useMemo(() => {
    return staff.filter((person) => {
      const haystack = `${person.first_name ?? ''} ${person.last_name ?? ''} ${person.email ?? ''}`.toLowerCase()
      return haystack.includes(search.toLowerCase())
    })
  }, [search, staff])

  if (loading) return <LoadingState label="Chargement du personnel..." />

  return (
    <div className="page-stack">
      <PageHeader
        title="Personnel"
        subtitle="Ressources humaines"
        badge={`${rows.length} résultat(s)`}
        actions={
          <>
            <input className="field-control" placeholder="Rechercher un agent..." value={search} onChange={(e) => setSearch(e.target.value)} />
            <button className="btn btn-primary" onClick={openModal}>+ Nouvel agent</button>
          </>
        }
      />

      <DataTable
        keyField="id"
        rows={rows}
        emptyTitle="Aucun membre du personnel"
        emptyDescription="La recherche ne correspond à aucun agent."
        columns={[
          { key: 'employee_id', label: 'Matricule', render: (row) => row.employee_id || '—' },
          { key: 'last_name', label: 'Nom', render: (row) => row.last_name?.toUpperCase() || '—' },
          { key: 'first_name', label: 'Prénom' },
          { key: 'email', label: 'Email', render: (row) => row.email || '—' },
          {
            key: 'roles',
            label: 'Rôles',
            render: (row) =>
              row.roles?.length ? (
                <div className="inline-badges">
                  {row.roles.map((role, index) => (
                    <span key={`${role}-${index}`} className="soft-badge">{role}</span>
                  ))}
                </div>
              ) : '—',
          },
          {
            key: 'is_active',
            label: 'Statut',
            render: (row) => (
              <StatusBadge variant={row.is_active ? 'success' : 'danger'}>
                {row.is_active ? 'Actif' : 'Inactif'}
              </StatusBadge>
            ),
          },
        ]}
      />

      {showModal && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && closeModal()}>
          <div className="modal-box">
            <div className="modal-header">
              <div>
                <p className="eyebrow">Ressources humaines</p>
                <h3>Ajouter un agent</h3>
              </div>
              <button className="modal-close" onClick={closeModal}>✕</button>
            </div>

            <form onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-grid">
                  <label>
                    <span>Prénom <span style={{ color: '#dc2626' }}>*</span></span>
                    <input name="first_name" className="field-control" value={form.first_name} onChange={handleField} required placeholder="Marie" />
                  </label>
                  <label>
                    <span>Nom <span style={{ color: '#dc2626' }}>*</span></span>
                    <input name="last_name" className="field-control" value={form.last_name} onChange={handleField} required placeholder="Dupont" />
                  </label>
                  <label className="field-full">
                    <span>Email <span style={{ color: '#dc2626' }}>*</span></span>
                    <input name="email" type="email" className="field-control" value={form.email} onChange={handleField} required placeholder="marie.dupont@hopital.fr" />
                  </label>
                  <label>
                    <span>Matricule</span>
                    <input name="employee_id" className="field-control" value={form.employee_id} onChange={handleField} placeholder="EMP013" />
                  </label>
                  <label>
                    <span>Téléphone</span>
                    <input name="phone" className="field-control" value={form.phone} onChange={handleField} placeholder="06 00 00 00 00" />
                  </label>
                  <label>
                    <span>Date d'embauche</span>
                    <input name="hire_date" type="date" className="field-control" value={form.hire_date} onChange={handleField} />
                  </label>
                  <label>
                    <span>Rôle</span>
                    <select name="role_id" className="field-control" value={form.role_id} onChange={handleField}>
                      <option value="">— Sélectionner —</option>
                      {roles.map((r) => (
                        <option key={r.id} value={r.id}>{r.name}</option>
                      ))}
                    </select>
                  </label>
                  <label className="field-full">
                    <span>Type de contrat <span style={{ color: '#dc2626' }}>*</span></span>
                    <select name="contract_type_id" className="field-control" value={form.contract_type_id} onChange={handleField} required>
                      <option value="">— Sélectionner un contrat —</option>
                      {contractTypes.map((ct) => (
                        <option key={ct.id} value={ct.id}>
                          {ct.name} — {ct.max_hours_per_week}h/sem
                          {ct.night_shift_allowed ? '' : ' (pas de nuit)'}
                        </option>
                      ))}
                    </select>
                  </label>

                  <div className="field-full" style={{ fontSize: '0.8rem', color: '#64748b', padding: '8px 0' }}>
                    Le contrat est requis pour la planification automatique. Les certifications et spécialités
                    peuvent être ajoutées depuis l'interface d'administration (écran Configuration).
                  </div>

                  {formError && (
                    <div className="result-box danger" style={{ gridColumn: '1 / -1' }}>
                      <p>{formError}</p>
                    </div>
                  )}
                </div>
              </div>

              <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
                <button type="button" className="btn btn-secondary" onClick={closeModal}>Annuler</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? 'Enregistrement...' : 'Créer l\'agent'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

function ShiftsPage() {
  const [shifts, setShifts] = useState([])
  const [loading, setLoading] = useState(true)
  const [modalShift, setModalShift] = useState(null)
  const [modalAssignments, setModalAssignments] = useState([])
  const [allStaff, setAllStaff] = useState([])
  const [selectedStaffId, setSelectedStaffId] = useState('')
  const [modalLoading, setModalLoading] = useState(false)
  const [modalError, setModalError] = useState('')

  const fetchShifts = async () => {
    try {
      const response = await api.get(endpoints.shifts)
      setShifts(normalizeListResponse(response.data))
    } catch (error) {
      console.error('Shifts loading error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchShifts() }, [])

  const openModal = async (shift) => {
    setModalShift(shift)
    setModalError('')
    setSelectedStaffId('')
    setModalLoading(true)
    try {
      const [assignRes, staffRes] = await Promise.all([
        api.get(`${endpoints.assignments}?shift=${shift.id}`),
        api.get(endpoints.staff),
      ])
      setModalAssignments(normalizeListResponse(assignRes.data))
      setAllStaff(normalizeListResponse(staffRes.data))
    } catch (error) {
      console.error('Modal loading error:', error)
    } finally {
      setModalLoading(false)
    }
  }

  const closeModal = () => {
    setModalShift(null)
    setModalAssignments([])
    setSelectedStaffId('')
    setModalError('')
  }

  const handleAdd = async () => {
    if (!selectedStaffId) return
    setModalError('')
    try {
      await api.post(endpoints.assignments, { staff: Number(selectedStaffId), shift: modalShift.id })
      const res = await api.get(`${endpoints.assignments}?shift=${modalShift.id}`)
      setModalAssignments(normalizeListResponse(res.data))
      setSelectedStaffId('')
      fetchShifts()
    } catch (error) {
      const msg = error.response?.data?.non_field_errors?.[0]
        || error.response?.data?.detail
        || 'Erreur lors de l\'affectation.'
      setModalError(msg)
    }
  }

  const handleRemove = async (assignmentId) => {
    setModalError('')
    try {
      await api.delete(`${endpoints.assignments}${assignmentId}/`)
      setModalAssignments((prev) => prev.filter((a) => a.id !== assignmentId))
      fetchShifts()
    } catch (error) {
      setModalError('Erreur lors de la suppression.')
    }
  }

  const assignedStaffIds = new Set(modalAssignments.map((a) => a.staff))
  const availableStaff = allStaff.filter((s) => !assignedStaffIds.has(s.id))

  if (loading) return <LoadingState label="Chargement des postes..." />

  return (
    <div className="page-stack">
      <PageHeader title="Postes" subtitle="Catalogue des vacations" badge={`${shifts.length} poste(s)`} />

      <DataTable
        keyField="id"
        rows={shifts}
        emptyTitle="Aucun poste disponible"
        emptyDescription="Aucun poste n'est actuellement enregistré."
        columns={[
          { key: 'service_name', label: 'Service', render: (row) => row.service_name || '—' },
          { key: 'care_unit_name', label: 'Unité', render: (row) => row.care_unit_name || '—' },
          {
            key: 'shift_type_name',
            label: 'Type',
            render: (row) => (
              <span className="type-pill" style={{ '--type-color': getShiftTypeColor(row.shift_type_name) }}>
                {row.shift_type_name || '—'}
              </span>
            ),
          },
          { key: 'start_datetime', label: 'Début', render: (row) => formatDateTime(row.start_datetime) },
          { key: 'end_datetime', label: 'Fin', render: (row) => formatDateTime(row.end_datetime) },
          {
            key: 'assigned_count',
            label: 'Couverture',
            render: (row) => (
              <StatusBadge variant={(row.assigned_count || 0) >= (row.min_staff || 0) ? 'success' : 'warning'}>
                {(row.assigned_count || 0)}/{row.max_staff}
              </StatusBadge>
            ),
          },
          {
            key: 'actions',
            label: '',
            render: (row) => (
              <button className="btn btn-sm btn-secondary" onClick={() => openModal(row)}>
                Affecter
              </button>
            ),
          },
        ]}
      />

      {modalShift && (
        <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && closeModal()}>
          <div className="modal-box">
            <div className="modal-header">
              <div>
                <p className="eyebrow">{modalShift.service_name} — {modalShift.care_unit_name}</p>
                <h3>
                  <span className="type-pill" style={{ '--type-color': getShiftTypeColor(modalShift.shift_type_name) }}>
                    {modalShift.shift_type_name}
                  </span>{' '}
                  {formatDateTime(modalShift.start_datetime).slice(0, 10)}
                  {' · '}
                  {formatDateTime(modalShift.start_datetime).slice(11, 16)} → {formatDateTime(modalShift.end_datetime).slice(11, 16)}
                </h3>
              </div>
              <button className="modal-close" onClick={closeModal}>✕</button>
            </div>

            <div className="modal-body">
              {modalLoading ? (
                <LoadingState label="Chargement..." />
              ) : (
                <>
                  <div className="modal-section">
                    <p className="modal-section-title">
                      Personnel affecté ({modalAssignments.length}/{modalShift.max_staff})
                    </p>
                    {modalAssignments.length ? (
                      <ul className="assignment-list">
                        {modalAssignments.map((a) => (
                          <li key={a.id} className="assignment-item">
                            <span>{a.staff_name || '—'}</span>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleRemove(a.id)}
                            >
                              Retirer
                            </button>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="muted-text">Aucun agent affecté pour le moment.</p>
                    )}
                  </div>

                  {modalAssignments.length < modalShift.max_staff && (
                    <div className="modal-section">
                      <p className="modal-section-title">Ajouter un agent</p>
                      <div className="modal-add-row">
                        <select
                          className="field-control"
                          value={selectedStaffId}
                          onChange={(e) => setSelectedStaffId(e.target.value)}
                        >
                          <option value="">— Sélectionner un agent —</option>
                          {availableStaff.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.last_name?.toUpperCase()} {s.first_name}
                              {s.roles?.length ? ` (${s.roles[0]})` : ''}
                            </option>
                          ))}
                        </select>
                        <button
                          className="btn btn-primary"
                          onClick={handleAdd}
                          disabled={!selectedStaffId}
                        >
                          Ajouter
                        </button>
                      </div>
                    </div>
                  )}

                  {modalError && (
                    <div className="result-box danger" style={{ marginTop: '12px' }}>
                      <p>{modalError}</p>
                    </div>
                  )}
                </>
              )}
            </div>

            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={closeModal}>Fermer</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function OptimizationPage() {
  const [config, setConfig] = useState({
    start_date: getWeekStartFromDate(),
    end_date: toDateKey(new Date(new Date(getWeekStartFromDate()).getTime() + 6 * 24 * 60 * 60 * 1000)),
    service_id: '',
  })
  const [services, setServices] = useState([])
  const [result, setResult] = useState(null)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await api.get(endpoints.services)
        setServices(normalizeListResponse(response.data))
      } catch (error) {
        console.error('Services loading error:', error)
      }
    }

    fetchServices()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setGenerating(true)
    setResult(null)

    try {
      const payload = {
        start_date: config.start_date,
        end_date: config.end_date,
      }

      if (config.service_id) {
        payload.service_id = config.service_id
      }

      const response = await api.post(endpoints.generate, payload)
      setResult(response.data)
    } catch (error) {
      setResult({
        status: 'error',
        error: error.response?.data?.error || error.message || 'Erreur inconnue',
      })
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="page-stack">
      <PageHeader title="Génération automatique" subtitle="Moteur d’optimisation" badge="Assistée" />

      <section className="optimization-layout">
        <div className="panel-card">
          <h3>Paramètres de génération</h3>
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              <span>Date de début</span>
              <input
                type="date"
                className="field-control"
                value={config.start_date}
                onChange={(e) => setConfig((current) => ({ ...current, start_date: e.target.value }))}
                required
              />
            </label>

            <label>
              <span>Date de fin</span>
              <input
                type="date"
                className="field-control"
                value={config.end_date}
                onChange={(e) => setConfig((current) => ({ ...current, end_date: e.target.value }))}
                required
              />
            </label>

            <label className="field-full">
              <span>Service concerné</span>
              <select
                className="field-control"
                value={config.service_id}
                onChange={(e) => setConfig((current) => ({ ...current, service_id: e.target.value }))}
              >
                <option value="">Tous les services</option>
                {services.map((service) => (
                  <option key={service.id} value={service.id}>
                    {service.name}
                  </option>
                ))}
              </select>
            </label>

            <button type="submit" className="btn btn-primary" disabled={generating}>
              {generating ? 'Génération en cours...' : 'Lancer la génération'}
            </button>
          </form>
        </div>

        <div className="panel-card">
          <h3>Résultat</h3>
          {result ? (
            result.status === 'error' ? (
              <div className="result-box danger">
                <strong>Échec de la génération</strong>
                <p>{result.error}</p>
              </div>
            ) : (
              <div className="result-stats">
                <div className="result-box success">
                  <strong>Génération terminée</strong>
                  <p>{result.message}</p>
                </div>
                <div className="mini-stats">
                  <StatCard label="Affectations" value={result.total_assignments ?? 0} hint="Créées automatiquement" tone="green" />
                  <StatCard label="Postes analysés" value={result.total_shifts ?? 0} hint="Dans la période choisie" tone="blue" />
                  <StatCard label="Couverture" value={`${result.coverage_rate ?? 0}%`} hint="Taux de remplissage" tone="amber" />
                  <StatCard label="Score" value={result.total_score ?? 0} hint="Équité / pénalités" tone="purple" />
                </div>
              </div>
            )
          ) : (
            <EmptyState
              title="Aucun résultat pour le moment"
              description="Configurez la période puis lancez l’organisation automatique du planning."
            />
          )}
        </div>
      </section>

      <section className="panel-card">
        <h3>Règles prises en compte</h3>
        <ul className="info-list">
          <li>Vérification des absences et des restrictions contractuelles.</li>
          <li>Recherche d’une meilleure répartition de la charge entre agents.</li>
          <li>Prise en compte des nuits consécutives et de la couverture minimale.</li>
        </ul>
      </section>
    </div>
  )
}

function ConfigPage() {
  const { isAuthenticated, isAdmin, login, user } = useAuth()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [isLoggingIn, setIsLoggingIn] = useState(false)
  const [loginError, setLoginError] = useState('')

  const adminBaseUrl = '/admin'

  const items = [
    {
      icon: '🏢',
      title: 'Services',
      href: `${adminBaseUrl}/core/service/`,
      description: 'Créer et organiser les pôles hospitaliers pris en charge par le planning.',
      action: 'Ouvrir la gestion des services',
    },
    {
      icon: '🏥',
      title: 'Unités de soin',
      href: `${adminBaseUrl}/core/careunit/`,
      description: 'Relier les unités à chaque service pour segmenter correctement les affectations.',
      action: 'Ouvrir les unités de soin',
    },
    {
      icon: '🕒',
      title: 'Types de poste',
      href: `${adminBaseUrl}/core/shifttype/`,
      description: 'Définir les horaires jour, soir, nuit et les règles de repos associées.',
      action: 'Configurer les types de poste',
    },
    {
      icon: '📆',
      title: "Types d'absence",
      href: `${adminBaseUrl}/core/absencetype/`,
      description: "Standardiser les motifs d'indisponibilité pris en compte par l'auto-planification.",
      action: 'Configurer les absences',
    },
    {
      icon: '📏',
      title: 'Règles métier',
      href: `${adminBaseUrl}/core/rule/`,
      description: "Ajuster les contraintes comme les nuits consécutives ou d'autres paramètres métier.",
      action: 'Gérer les règles métier',
    },
    {
      icon: '🤖',
      title: 'Configuration optimisation',
      href: `${adminBaseUrl}/optimization/optimizationconfig/`,
      description: 'Modifier les poids et paramètres utilisés par le moteur de génération automatique.',
      action: 'Ouvrir la configuration IA',
    },
  ]

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoginError('')
    setIsLoggingIn(true)

    const result = await login(username, password)
    setIsLoggingIn(false)

    if (!result.success) {
      setLoginError(result.error)
    }
  }

  const isAdminUser = isAuthenticated && isAdmin

  return (
    <div className="page-stack">
      <PageHeader
        title="Configuration"
        subtitle="Paramètres avancés"
        badge={`${items.length} modules disponibles`}
      />

      {!isAuthenticated ? (
        <section className="panel-card">
          <h3>Connexion administrateur</h3>
          <p className="section-text">
            Cette application n'est pas l'interface d'administration Django elle-même. L'écran
            configuration sert de passerelle vers l'espace admin du backend. Pour accéder aux modules
            ci-dessous, connectez-vous avec un compte administrateur.
          </p>

          <form className="form-grid" onSubmit={handleLogin} style={{ maxWidth: '400px', marginTop: '20px' }}>
            <label>
              <span>Nom d'utilisateur</span>
              <input
                type="text"
                className="field-control"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                required
              />
            </label>

            <label>
              <span>Mot de passe</span>
              <input
                type="password"
                className="field-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
            </label>

            {loginError && (
              <div className="result-box danger" style={{ gridColumn: '1 / -1' }}>
                <p>{loginError}</p>
              </div>
            )}

            <button type="submit" className="btn btn-primary" disabled={isLoggingIn}>
              {isLoggingIn ? 'Connexion...' : "Se connecter en tant qu'admin"}
            </button>
          </form>
        </section>
      ) : isAdminUser ? (
        <section className="panel-card">
          <h3>Accès administrateur actif</h3>
          <p className="section-text">
            Vous êtes connecté en tant qu'administrateur. Vous pouvez accéder aux modules de configuration
            ci-dessous. Les liens s'ouvriront dans un nouvel onglet vers l'interface d'administration Django.
          </p>
          <div style={{ marginTop: '16px', padding: '12px 16px', backgroundColor: '#f0fdf4', borderRadius: '8px', border: '1px solid #bbf7d0' }}>
            <strong style={{ color: '#166534' }}>✓ Connecté en tant que {user.first_name ? `${user.first_name} ${user.last_name}` : user.username}</strong>
          </div>
        </section>
      ) : (
        <section className="panel-card">
          <h3>Compte non administrateur</h3>
          <p className="section-text">
            Vous êtes connecté, mais votre compte n'a pas les privilèges d'administrateur nécessaires
            pour accéder aux modules de configuration. Veuillez vous déconnecter et vous reconnecter
            avec un compte administrateur.
          </p>
        </section>
      )}

      {isAdminUser && (
        <section className="config-grid">
          {items.map((item) => (
            <a key={item.title} href={item.href} className="config-card" target="_blank" rel="noreferrer">
              <span className="config-icon">{item.icon}</span>
              <strong>{item.title}</strong>
              <p>{item.description}</p>
              <span className="config-link">{item.action} →</span>
            </a>
          ))}
        </section>
      )}
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/planning" element={<PlanningPage />} />
          <Route path="/staff" element={<StaffPage />} />
          <Route path="/shifts" element={<ShiftsPage />} />
          <Route path="/optimization" element={<OptimizationPage />} />
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

export default App
