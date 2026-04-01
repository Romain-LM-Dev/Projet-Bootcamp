import { useState, useEffect, useCallback } from "react";
import { api } from "./api";

// ─── ICONS ────────────────────────────────────────────────────────────────────
const IconUser    = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>;
const IconShift   = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>;
const IconLink    = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>;
const IconAbsence = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;
const IconClose   = () => <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>;
const IconCheck   = () => <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>;
const IconPlus    = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const IconTrash   = () => <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/></svg>;
const IconSpinner = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: "spin 0.8s linear infinite" }}><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>;

// ─── COMPOSANTS ──────────────────────────────────────────────────────────────

function Badge({ children, color = "slate" }) {
  const map = {
    green:  "background:#d1fae5;color:#065f46",
    red:    "background:#fee2e2;color:#991b1b",
    blue:   "background:#dbeafe;color:#1e40af",
    amber:  "background:#fef3c7;color:#92400e",
    slate:  "background:#f1f5f9;color:#475569",
    purple: "background:#ede9fe;color:#5b21b6",
  };
  const styles = Object.fromEntries(
    map[color].split(";").map(p => {
      const [k, v] = p.split(":");
      return [k.trim().replace(/-([a-z])/g, g => g[1].toUpperCase()), v.trim()];
    })
  );
  return <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 99, letterSpacing: "0.04em", ...styles }}>{children}</span>;
}

function Modal({ title, onClose, children }) {
  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(15,23,42,0.55)", backdropFilter: "blur(4px)", zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center" }}>
      <div style={{ background: "var(--card)", borderRadius: 16, padding: 28, width: 480, maxWidth: "90vw", boxShadow: "0 24px 64px rgba(0,0,0,0.2)", border: "1px solid var(--border)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>{title}</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--muted)", padding: 4, borderRadius: 6, display: "flex" }}><IconClose /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Toast({ message, type, onClose }) {
  useEffect(() => { const t = setTimeout(onClose, 5000); return () => clearTimeout(t); }, []);
  const isErr = type === "error";
  return (
    <div style={{ position: "fixed", bottom: 24, right: 24, zIndex: 200, background: isErr ? "#1e1e1e" : "#022c22", border: `1px solid ${isErr ? "#ef4444" : "#10b981"}`, borderRadius: 12, padding: "14px 18px", display: "flex", gap: 10, alignItems: "flex-start", maxWidth: 400, boxShadow: "0 8px 32px rgba(0,0,0,0.3)" }}>
      <span style={{ color: isErr ? "#ef4444" : "#10b981", marginTop: 1 }}>{isErr ? <IconClose /> : <IconCheck />}</span>
      <span style={{ fontSize: 13, color: "#e2e8f0", lineHeight: 1.5 }}>{message}</span>
    </div>
  );
}

function LoadingState({ text = "Chargement…" }) {
  return (
    <div style={{ textAlign: "center", padding: "60px 0", color: "var(--muted)", display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
      <IconSpinner />
      <span style={{ fontSize: 14 }}>{text}</span>
    </div>
  );
}

function ErrorState({ message, onRetry }) {
  return (
    <div style={{ textAlign: "center", padding: "60px 0", color: "#b91c1c" }}>
      <div style={{ fontSize: 14, marginBottom: 12 }}>⚠️ {message}</div>
      {onRetry && <button onClick={onRetry} style={{ fontSize: 13, padding: "8px 16px", borderRadius: 8, border: "1px solid #fca5a5", background: "#fef2f2", color: "#b91c1c", cursor: "pointer" }}>Réessayer</button>}
    </div>
  );
}

const inputStyle = { width: "100%", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", fontSize: 14, color: "var(--text)", boxSizing: "border-box", outline: "none", marginBottom: 12, fontFamily: "inherit" };
const selectStyle = { ...inputStyle };

// ─── PAGE SOIGNANTS ──────────────────────────────────────────────────────────

function StaffPage({ toast }) {
  const [staff, setStaff]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm]       = useState({ first_name: "", last_name: "", email: "", phone: "", is_active: true });
  const [saving, setSaving]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setStaff(await api.staff.list()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const openAdd  = () => { setEditing(null); setForm({ first_name: "", last_name: "", email: "", phone: "", is_active: true }); setShowModal(true); };
  const openEdit = (s)  => { setEditing(s); setForm({ first_name: s.first_name, last_name: s.last_name, email: s.email, phone: s.phone ?? "", is_active: s.is_active }); setShowModal(true); };

  const handleSave = async () => {
    if (!form.first_name || !form.last_name || !form.email) return;
    setSaving(true);
    try {
      if (editing) {
        const updated = await api.staff.update(editing.id, form);
        setStaff(prev => prev.map(s => s.id === editing.id ? updated : s));
        toast("Soignant mis à jour.", "success");
      } else {
        const created = await api.staff.create(form);
        setStaff(prev => [...prev, created]);
        toast("Soignant ajouté.", "success");
      }
      setShowModal(false);
    } catch (e) {
      toast(e.message, "error");
    } finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    if (!confirm("Supprimer ce soignant ?")) return;
    try {
      await api.staff.delete(id);
      setStaff(prev => prev.filter(s => s.id !== id));
      toast("Soignant supprimé.", "success");
    } catch (e) { toast(e.message, "error"); }
  };

  if (loading) return <LoadingState />;
  if (error)   return <ErrorState message={error} onRetry={load} />;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Soignants</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>{staff.filter(s => s.is_active).length} actifs · {staff.length} au total</p>
        </div>
        <button onClick={openAdd} style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--accent)", color: "#fff", border: "none", borderRadius: 10, padding: "9px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
          <IconPlus /> Nouveau soignant
        </button>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        {staff.map(s => (
          <div key={s.id} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 40, height: 40, borderRadius: 12, background: s.is_active ? "var(--accent-soft)" : "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, fontWeight: 700, fontSize: 14 }}>
              {s.first_name[0]}{s.last_name[0]}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>{s.first_name} {s.last_name}</span>
                <Badge color={s.is_active ? "green" : "slate"}>{s.is_active ? "Actif" : "Inactif"}</Badge>
                {s.roles?.map(r => <Badge key={r} color="blue">{r}</Badge>)}
              </div>
              <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>
                {s.specialties?.join(", ")} · {s.email}
              </div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button onClick={() => openEdit(s)} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 12px", fontSize: 12, cursor: "pointer", fontWeight: 500 }}>Modifier</button>
              <button onClick={() => handleDelete(s.id)} style={{ background: "none", border: "1px solid #fecaca", borderRadius: 8, padding: "6px 10px", color: "#ef4444", cursor: "pointer", display: "flex", alignItems: "center" }}><IconTrash /></button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <Modal title={editing ? "Modifier le soignant" : "Nouveau soignant"} onClose={() => setShowModal(false)}>
          {["first_name", "last_name", "email", "phone"].map(field => (
            <div key={field}>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>{field.replace("_", " ")}</label>
              <input value={form[field] || ""} onChange={e => setForm(p => ({ ...p, [field]: e.target.value }))} style={inputStyle} />
            </div>
          ))}
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer", marginBottom: 20 }}>
            <input type="checkbox" checked={form.is_active} onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))} />
            Soignant actif
          </label>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button onClick={() => setShowModal(false)} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 16px", fontSize: 13, cursor: "pointer" }}>Annuler</button>
            <button onClick={handleSave} disabled={saving} style={{ background: "var(--accent)", color: "#fff", border: "none", borderRadius: 8, padding: "9px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
              {saving && <IconSpinner />} Enregistrer
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── PAGE POSTES ──────────────────────────────────────────────────────────────

function ShiftsPage({ toast }) {
  const [shifts, setShifts]   = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try { setShifts(await api.shifts.list()); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleDelete = async (id) => {
    if (!confirm("Supprimer ce poste ?")) return;
    try {
      await api.shifts.delete(id);
      setShifts(prev => prev.filter(s => s.id !== id));
      toast("Poste supprimé.", "success");
    } catch (e) { toast(e.message, "error"); }
  };

  const typeColor = (name = "") => {
    if (name.toLowerCase().includes("nuit")) return "purple";
    if (name.toLowerCase().includes("jour")) return "blue";
    return "slate";
  };

  if (loading) return <LoadingState />;
  if (error)   return <ErrorState message={error} onRetry={load} />;

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Postes de garde</h2>
        <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>{shifts.length} poste{shifts.length !== 1 ? "s" : ""}</p>
      </div>
      <div style={{ display: "grid", gap: 10 }}>
        {shifts.map(s => (
          <div key={s.id} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap", marginBottom: 4 }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>{s.label}</span>
                <Badge color={typeColor(s.shift_type_name)}>{s.shift_type_name}</Badge>
                <Badge color={s.assigned_count >= s.min_staff ? "green" : "amber"}>
                  {s.assigned_count}/{s.min_staff} min
                </Badge>
              </div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>
                {new Date(s.start_datetime).toLocaleString("fr-MA")} → {new Date(s.end_datetime).toLocaleString("fr-MA")}
              </div>
              {s.required_certifications?.length > 0 && (
                <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
                  {s.required_certifications.map(c => <Badge key={c.id} color="slate">🏅 {c.name}</Badge>)}
                </div>
              )}
            </div>
            <button onClick={() => handleDelete(s.id)} style={{ background: "none", border: "1px solid #fecaca", borderRadius: 8, padding: "6px 10px", color: "#ef4444", cursor: "pointer", display: "flex", alignItems: "center" }}><IconTrash /></button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── PAGE AFFECTATIONS ────────────────────────────────────────────────────────

function AssignmentsPage({ toast }) {
  const [staff, setStaff]               = useState([]);
  const [shifts, setShifts]             = useState([]);
  const [assignments, setAssignments]   = useState([]);
  const [loading, setLoading]           = useState(true);
  const [selectedStaff, setSelectedStaff] = useState("");
  const [selectedShift, setSelectedShift] = useState("");
  const [assigning, setAssigning]       = useState(false);
  const [constraintError, setConstraintError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, sh, a] = await Promise.all([api.staff.list(), api.shifts.list(), api.assignments.list()]);
      setStaff(s); setShifts(sh); setAssignments(a);
    } catch (e) { toast(e.message, "error"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleAssign = async () => {
    if (!selectedStaff || !selectedShift) return;
    setAssigning(true); setConstraintError(null);
    try {
      const created = await api.assignments.create(parseInt(selectedStaff), parseInt(selectedShift));
      setAssignments(prev => [created, ...prev]);
      toast("✅ Affectation enregistrée.", "success");
      setSelectedStaff(""); setSelectedShift("");
    } catch (e) {
      if (e.status === 409 && e.payload) {
        setConstraintError(e.payload);
      } else {
        toast(e.message, "error");
      }
    } finally { setAssigning(false); }
  };

  const handleRemove = async (id) => {
    try {
      await api.assignments.delete(id);
      setAssignments(prev => prev.filter(a => a.id !== id));
      toast("Affectation supprimée.", "success");
    } catch (e) { toast(e.message, "error"); }
  };

  if (loading) return <LoadingState />;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "360px 1fr", gap: 24, alignItems: "start" }}>
      {/* Formulaire */}
      <div style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 16, padding: 24 }}>
        <h3 style={{ margin: "0 0 20px", fontSize: 15, fontWeight: 700 }}>Nouvelle affectation</h3>

        <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Soignant</label>
        <select value={selectedStaff} onChange={e => { setSelectedStaff(e.target.value); setConstraintError(null); }} style={{ ...selectStyle, marginBottom: 16 }}>
          <option value="">— Choisir un soignant —</option>
          {staff.map(s => <option key={s.id} value={s.id}>{s.first_name} {s.last_name} ({s.roles?.join(", ") || "—"})</option>)}
        </select>

        <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.05em" }}>Poste de garde</label>
        <select value={selectedShift} onChange={e => { setSelectedShift(e.target.value); setConstraintError(null); }} style={{ ...selectStyle, marginBottom: 20 }}>
          <option value="">— Choisir un poste —</option>
          {shifts.map(s => <option key={s.id} value={s.id}>{s.label}</option>)}
        </select>

        {/* Affichage de la violation de contrainte */}
        {constraintError && (
          <div style={{ marginBottom: 16, padding: "12px 14px", borderRadius: 10, background: "#fef2f2", border: "1px solid #fca5a5" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#9b1c1c", letterSpacing: "0.05em", marginBottom: 4 }}>
              CONTRAINTE {constraintError.code} VIOLÉE
            </div>
            <div style={{ fontSize: 13, color: "#b91c1c", lineHeight: 1.5 }}>
              {constraintError.detail}
            </div>
          </div>
        )}

        <button
          onClick={handleAssign}
          disabled={!selectedStaff || !selectedShift || assigning}
          style={{ width: "100%", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 8, padding: "10px", fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, opacity: (!selectedStaff || !selectedShift) ? 0.5 : 1 }}
        >
          {assigning && <IconSpinner />} Affecter
        </button>
      </div>

      {/* Liste des affectations */}
      <div>
        <div style={{ marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 700 }}>Affectations existantes</h3>
          <p style={{ margin: "3px 0 0", fontSize: 13, color: "var(--muted)" }}>{assignments.length} affectation{assignments.length !== 1 ? "s" : ""}</p>
        </div>
        {assignments.length === 0 && (
          <div style={{ textAlign: "center", padding: "40px 0", color: "var(--muted)", fontSize: 14 }}>Aucune affectation pour l'instant.</div>
        )}
        <div style={{ display: "grid", gap: 8 }}>
          {assignments.map(a => (
            <div key={a.id} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "12px 16px", display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 36, height: 36, borderRadius: 10, background: "var(--accent-soft)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, flexShrink: 0, fontWeight: 700 }}>
                {a.staff_name?.split(" ").map(n => n[0]).join("") ?? "??"}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{a.staff_name}</div>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>{a.shift_label}</div>
              </div>
              <button onClick={() => handleRemove(a.id)} style={{ background: "none", border: "1px solid #fecaca", borderRadius: 8, padding: "5px 8px", color: "#ef4444", cursor: "pointer", display: "flex", alignItems: "center" }}><IconTrash /></button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── PAGE ABSENCES ────────────────────────────────────────────────────────────

function AbsencesPage({ toast }) {
  const [absences, setAbsences]   = useState([]);
  const [staff, setStaff]         = useState([]);
  const [absenceTypes, setAbsenceTypes] = useState([]);
  const [loading, setLoading]     = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm]           = useState({ staff: "", absence_type: "", start_date: "", expected_end_date: "", is_planned: true });
  const [saving, setSaving]       = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [a, s, at] = await Promise.all([api.absences.list(), api.staff.list(), api.absenceTypes()]);
      setAbsences(a); setStaff(s); setAbsenceTypes(at);
    } catch (e) { toast(e.message, "error"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    if (!form.staff || !form.absence_type || !form.start_date || !form.expected_end_date) return;
    setSaving(true);
    try {
      const created = await api.absences.create(form);
      setAbsences(prev => [created, ...prev]);
      toast("Absence déclarée.", "success");
      setShowModal(false);
      setForm({ staff: "", absence_type: "", start_date: "", expected_end_date: "", is_planned: true });
    } catch (e) { toast(e.message, "error"); }
    finally { setSaving(false); }
  };

  const handleDelete = async (id) => {
    try {
      await api.absences.delete(id);
      setAbsences(prev => prev.filter(a => a.id !== id));
      toast("Absence supprimée.", "success");
    } catch (e) { toast(e.message, "error"); }
  };

  if (loading) return <LoadingState />;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Absences</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>{absences.length} absence{absences.length !== 1 ? "s" : ""} enregistrée{absences.length !== 1 ? "s" : ""}</p>
        </div>
        <button onClick={() => setShowModal(true)} style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--accent)", color: "#fff", border: "none", borderRadius: 10, padding: "9px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer" }}>
          <IconPlus /> Déclarer une absence
        </button>
      </div>

      <div style={{ display: "grid", gap: 10 }}>
        {absences.map(a => (
          <div key={a.id} style={{ background: "var(--card)", border: "1px solid var(--border)", borderRadius: 12, padding: "14px 18px", display: "flex", alignItems: "center", gap: 14 }}>
            <div style={{ width: 40, height: 40, borderRadius: 12, background: "#fef3c7", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>⚠️</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, fontSize: 14 }}>{a.staff_name}</div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>
                {a.absence_type_name} · du {a.start_date} au {a.expected_end_date}
                {a.is_planned ? "" : " · Non planifiée"}
              </div>
            </div>
            <button onClick={() => handleDelete(a.id)} style={{ background: "none", border: "1px solid #fecaca", borderRadius: 8, padding: "5px 8px", color: "#ef4444", cursor: "pointer", display: "flex", alignItems: "center" }}><IconTrash /></button>
          </div>
        ))}
      </div>

      {showModal && (
        <Modal title="Déclarer une absence" onClose={() => setShowModal(false)}>
          <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Soignant</label>
          <select value={form.staff} onChange={e => setForm(p => ({ ...p, staff: e.target.value }))} style={selectStyle}>
            <option value="">— Choisir —</option>
            {staff.map(s => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
          </select>
          <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Type d'absence</label>
          <select value={form.absence_type} onChange={e => setForm(p => ({ ...p, absence_type: e.target.value }))} style={selectStyle}>
            <option value="">— Choisir —</option>
            {absenceTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Date de début</label>
          <input type="date" value={form.start_date} onChange={e => setForm(p => ({ ...p, start_date: e.target.value }))} style={inputStyle} />
          <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" }}>Date de fin prévue</label>
          <input type="date" value={form.expected_end_date} onChange={e => setForm(p => ({ ...p, expected_end_date: e.target.value }))} style={inputStyle} />
          <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer", marginBottom: 20 }}>
            <input type="checkbox" checked={form.is_planned} onChange={e => setForm(p => ({ ...p, is_planned: e.target.checked }))} />
            Absence planifiée
          </label>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <button onClick={() => setShowModal(false)} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 16px", fontSize: 13, cursor: "pointer" }}>Annuler</button>
            <button onClick={handleSave} disabled={saving} style={{ background: "var(--accent)", color: "#fff", border: "none", borderRadius: 8, padding: "9px 16px", fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", gap: 6 }}>
              {saving && <IconSpinner />} Enregistrer
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage]       = useState("assignments");
  const [toastMsg, setToastMsg] = useState(null);

  const toast = useCallback((message, type) => setToastMsg({ message, type }), []);

  const nav = [
    { id: "staff",       label: "Soignants",   icon: <IconUser /> },
    { id: "shifts",      label: "Postes",       icon: <IconShift /> },
    { id: "assignments", label: "Affectations", icon: <IconLink /> },
    { id: "absences",    label: "Absences",     icon: <IconAbsence /> },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
          --bg: #f8fafc;
          --card: #ffffff;
          --surface: #f1f5f9;
          --border: #e2e8f0;
          --text: #0f172a;
          --muted: #64748b;
          --accent: #2563eb;
          --accent-soft: #eff6ff;
          --nav-w: 220px;
        }
        body { font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); }
        h1, h2, h3, h4 { font-family: 'Syne', sans-serif; }
        select, input, button { font-family: inherit; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh" }}>
        {/* Sidebar */}
        <nav style={{ width: "var(--nav-w)", background: "var(--card)", borderRight: "1px solid var(--border)", display: "flex", flexDirection: "column", padding: "24px 16px", flexShrink: 0, position: "sticky", top: 0, height: "100vh" }}>
          <div style={{ marginBottom: 32, padding: "0 8px" }}>
            <div style={{ width: 36, height: 36, background: "var(--accent)", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 10 }}>
              <svg width="20" height="20" fill="none" stroke="#fff" strokeWidth="2" viewBox="0 0 24 24"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
            </div>
            <div style={{ fontSize: 15, fontWeight: 800, fontFamily: "Syne, sans-serif" }}>PlanningRH</div>
            <div style={{ fontSize: 11, color: "var(--muted)", marginTop: 1 }}>Hôpital · v2.0</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
            {nav.map(n => (
              <button key={n.id} onClick={() => setPage(n.id)}
                style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", borderRadius: 10, border: "none", cursor: "pointer", fontSize: 13, fontWeight: page === n.id ? 600 : 400, background: page === n.id ? "var(--accent-soft)" : "transparent", color: page === n.id ? "var(--accent)" : "var(--muted)", textAlign: "left", transition: "all 0.15s" }}>
                <span style={{ color: page === n.id ? "var(--accent)" : "var(--muted)" }}>{n.icon}</span>
                {n.label}
              </button>
            ))}
          </div>
          <div style={{ marginTop: "auto", padding: "16px 8px 0", borderTop: "1px solid var(--border)" }}>
            <div style={{ fontSize: 11, color: "var(--muted)", lineHeight: 1.7 }}>
              <div style={{ fontWeight: 600, marginBottom: 4, color: "var(--text)", fontSize: 12 }}>Contraintes actives</div>
              {["C1 – Soignant actif", "C2 – Absence", "C3 – Certifications", "C4 – Contrat / nuit", "C5 – Chevauchement", "C6 – Repos post-nuit", "C7 – Quota horaire", "C8 – Préférences"].map(c => (
                <div key={c}>{c}</div>
              ))}
            </div>
          </div>
        </nav>

        {/* Main */}
        <main style={{ flex: 1, padding: 32, overflowY: "auto" }}>
          {page === "staff"       && <StaffPage toast={toast} />}
          {page === "shifts"      && <ShiftsPage toast={toast} />}
          {page === "assignments" && <AssignmentsPage toast={toast} />}
          {page === "absences"    && <AbsencesPage toast={toast} />}
        </main>
      </div>

      {toastMsg && <Toast message={toastMsg.message} type={toastMsg.type} onClose={() => setToastMsg(null)} />}
    </>
  );
}
