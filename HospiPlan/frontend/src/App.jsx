import { useState, useEffect, useCallback, useMemo } from "react";
import { api } from "./api";

// ─── ICONS ────────────────────────────────────────────────────────────────────
const IconUser     = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>;
const IconShift    = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>;
const IconLink     = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>;
const IconAbsence  = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>;
const IconCalendar = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/><line x1="8" y1="14" x2="8.01" y2="14"/><line x1="12" y1="14" x2="12.01" y2="14"/><line x1="16" y1="14" x2="16.01" y2="14"/></svg>;
const IconClose    = () => <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>;
const IconCheck    = () => <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>;
const IconPlus     = () => <svg width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>;
const IconTrash    = () => <svg width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6m4-6v6"/><path d="M9 6V4h6v2"/></svg>;
const IconSpinner  = () => <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" style={{ animation: "spin 0.8s linear infinite" }}><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>;

// ─── COMPOSANTS PARTAGÉS ─────────────────────────────────────────────────────

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
  useEffect(() => { const t = setTimeout(onClose, 5000); return () => clearTimeout(t); }, [onClose]);
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

const inputStyle  = { width: "100%", background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "9px 12px", fontSize: 14, color: "var(--text)", boxSizing: "border-box", outline: "none", marginBottom: 12, fontFamily: "inherit" };
const selectStyle = { ...inputStyle };
const labelStyle  = { display: "block", fontSize: 11, fontWeight: 600, color: "var(--muted)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.05em" };

// ─── Composants utilitaires pour le formulaire ──────────────────────────────

function SectionTitle({ children }) {
  return (
    <div style={{
      fontSize: 11, fontWeight: 700, color: "var(--accent)",
      marginTop: 20, marginBottom: 10, paddingBottom: 6,
      borderBottom: "1px solid var(--border)",
      textTransform: "uppercase", letterSpacing: "0.06em",
    }}>
      {children}
    </div>
  );
}

function ChipSelect({ items, selected, onChange, labelKey = "name" }) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
      {items.map(item => {
        const active = selected.includes(item.id);
        return (
          <label key={item.id} style={{
            display: "flex", alignItems: "center", gap: 6,
            fontSize: 13, cursor: "pointer", padding: "6px 12px",
            borderRadius: 8, transition: "all 0.15s", userSelect: "none",
            border: `1.5px solid ${active ? "var(--accent)" : "var(--border)"}`,
            background: active ? "var(--accent-soft)" : "transparent",
            color: active ? "var(--accent)" : "var(--text)",
            fontWeight: active ? 600 : 400,
          }}>
            <input type="checkbox" checked={active}
              onChange={() => onChange(item.id)}
              style={{ display: "none" }} />
            {active && <IconCheck />}
            {item[labelKey]}
          </label>
        );
      })}
      {items.length === 0 && (
        <span style={{ fontSize: 12, color: "var(--muted)", fontStyle: "italic" }}>
          Aucun disponible — créez-en d'abord via l'admin Django
        </span>
      )}
    </div>
  );
}

// ─── PAGE SOIGNANTS (enrichie) ──────────────────────────────────────────────

function StaffPage({ toast }) {
  const [staff, setStaff]         = useState([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing]     = useState(null);
  const [saving, setSaving]       = useState(false);

  // Données de référence
  const [roles, setRoles]                   = useState([]);
  const [specialties, setSpecialties]       = useState([]);
  const [certifications, setCertifications] = useState([]);
  const [contractTypes, setContractTypes]   = useState([]);

  // Formulaire principal
  const emptyForm = {
    first_name: "", last_name: "", email: "", phone: "", is_active: true,
    role_ids: [],
    specialty_ids: [],
  };
  const [form, setForm] = useState(emptyForm);

  // Certifications à associer
  const emptyCertLine = { certification_id: "", obtained_date: "", expiration_date: "" };
  const [certLines, setCertLines] = useState([]);

  // Contrat — adapté au modèle Django (workload_percent, pas weekly_hours)
  const emptyContract = {
    contract_type: "", start_date: "", end_date: "",
    workload_percent: "100",
  };
  const [contractForm, setContractForm] = useState(emptyContract);

  // ── Chargement ────────────────────────────────────────────────
  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const results = await Promise.allSettled([
        api.staff.list(),
        api.roles(),
        api.specialties(),
        api.certifications(),
        api.contractTypes(),
      ]);
      const val = (r) => r.status === "fulfilled" ? r.value : [];
      setStaff(val(results[0]));
      setRoles(val(results[1]));
      setSpecialties(val(results[2]));
      setCertifications(val(results[3]));
      setContractTypes(val(results[4]));
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  // ── Helpers formulaire ────────────────────────────────────────
  const toggleId = (field, id) => {
    setForm(prev => ({
      ...prev,
      [field]: prev[field].includes(id)
        ? prev[field].filter(x => x !== id)
        : [...prev[field], id],
    }));
  };

  const addCertLine    = () => setCertLines(prev => [...prev, { ...emptyCertLine }]);
  const removeCertLine = (i) => setCertLines(prev => prev.filter((_, idx) => idx !== i));
  const updateCertLine = (i, field, value) =>
    setCertLines(prev => prev.map((c, idx) => idx === i ? { ...c, [field]: value } : c));

  // ── Ouverture modale ──────────────────────────────────────────
  const openAdd = () => {
    setEditing(null);
    setForm(emptyForm);
    setCertLines([]);
    setContractForm(emptyContract);
    setShowModal(true);
  };

  const openEdit = (s) => {
    setEditing(s);
    setForm({
      first_name: s.first_name,
      last_name: s.last_name,
      email: s.email,
      phone: s.phone ?? "",
      is_active: s.is_active,
      role_ids: (s.roles || []).map(r =>
        typeof r === "object" ? r.id : roles.find(x => x.name === r)?.id
      ).filter(Boolean),
      specialty_ids: (s.specialties || []).map(sp =>
        typeof sp === "object" ? sp.id : specialties.find(x => x.name === sp)?.id
      ).filter(Boolean),
    });
    setCertLines([]);
    setContractForm(emptyContract);
    setShowModal(true);
  };

  // ── Sauvegarde ────────────────────────────────────────────────
  const handleSave = async () => {
    if (!form.first_name || !form.last_name || !form.email) {
      toast("Prénom, nom et email sont requis.", "error");
      return;
    }
    setSaving(true);
    try {
      const payload = {
        first_name:  form.first_name,
        last_name:   form.last_name,
        email:       form.email,
        phone:       form.phone,
        is_active:   form.is_active,
        roles:       form.role_ids,
        specialties: form.specialty_ids,
      };

      let staffData;
      if (editing) {
        staffData = await api.staff.update(editing.id, payload);
        setStaff(prev => prev.map(s => s.id === editing.id ? staffData : s));
      } else {
        staffData = await api.staff.create(payload);
        setStaff(prev => [...prev, staffData]);
      }

      // Créer les certifications associées
      for (const cert of certLines) {
        if (cert.certification_id && cert.obtained_date) {
          try {
            await api.staffCertifications.create({
              staff:           staffData.id,
              certification:   parseInt(cert.certification_id),
              obtained_date:   cert.obtained_date,
              expiration_date: cert.expiration_date || null,
            });
          } catch (e) {
            toast(`Certification : ${e.message}`, "error");
          }
        }
      }

      // Créer le contrat
      if (contractForm.contract_type && contractForm.start_date) {
        try {
          await api.contracts.create({
            staff:            staffData.id,
            contract_type:    parseInt(contractForm.contract_type),
            start_date:       contractForm.start_date,
            end_date:         contractForm.end_date || null,
            workload_percent: parseInt(contractForm.workload_percent) || 100,
          });
        } catch (e) {
          toast(`Contrat : ${e.message}`, "error");
        }
      }

      toast(
        editing ? "Soignant mis à jour ✓" : "Soignant créé avec toutes ses données ✓",
        "success"
      );
      setShowModal(false);
      load();
    } catch (e) {
      toast(e.message, "error");
    } finally {
      setSaving(false);
    }
  };

  // ── Suppression ───────────────────────────────────────────────
  const handleDelete = async (id) => {
    if (!confirm("Supprimer ce soignant et toutes ses données associées ?")) return;
    try {
      await api.staff.delete(id);
      setStaff(prev => prev.filter(s => s.id !== id));
      toast("Soignant supprimé.", "success");
    } catch (e) { toast(e.message, "error"); }
  };

  // ── Rendu ─────────────────────────────────────────────────────
  if (loading) return <LoadingState />;
  if (error)   return <ErrorState message={error} onRetry={load} />;

  return (
    <div>
      {/* En-tête */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Soignants</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>
            {staff.filter(s => s.is_active).length} actifs · {staff.length} au total
          </p>
        </div>
        <button onClick={openAdd} style={{
          display: "flex", alignItems: "center", gap: 6,
          background: "var(--accent)", color: "#fff", border: "none",
          borderRadius: 10, padding: "9px 16px", fontSize: 13,
          fontWeight: 600, cursor: "pointer",
        }}>
          <IconPlus /> Nouveau soignant
        </button>
      </div>

      {/* Liste */}
      <div style={{ display: "grid", gap: 10 }}>
        {staff.map(s => (
          <div key={s.id} style={{
            background: "var(--card)", border: "1px solid var(--border)",
            borderRadius: 12, padding: "14px 18px",
            display: "flex", alignItems: "center", gap: 14,
          }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: s.is_active ? "var(--accent-soft)" : "#f1f5f9",
              display: "flex", alignItems: "center", justifyContent: "center",
              flexShrink: 0, fontWeight: 700, fontSize: 14,
            }}>
              {s.first_name[0]}{s.last_name[0]}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span style={{ fontWeight: 700, fontSize: 14 }}>{s.first_name} {s.last_name}</span>
                <Badge color={s.is_active ? "green" : "slate"}>{s.is_active ? "Actif" : "Inactif"}</Badge>
                {(s.roles || []).map(r => (
                  <Badge key={typeof r === "object" ? r.id : r} color="blue">
                    {typeof r === "object" ? r.name : r}
                  </Badge>
                ))}
              </div>
              <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 3 }}>
                {(s.specialties || []).map(sp => typeof sp === "object" ? sp.name : sp).join(", ")}
                {s.specialties?.length > 0 && " · "}
                {s.email}
              </div>
            </div>
            <div style={{ display: "flex", gap: 6 }}>
              <button onClick={() => openEdit(s)} style={{
                background: "var(--surface)", border: "1px solid var(--border)",
                borderRadius: 8, padding: "6px 12px", fontSize: 12,
                cursor: "pointer", fontWeight: 500,
              }}>Modifier</button>
              <button onClick={() => handleDelete(s.id)} style={{
                background: "none", border: "1px solid #fecaca",
                borderRadius: 8, padding: "6px 10px", color: "#ef4444",
                cursor: "pointer", display: "flex", alignItems: "center",
              }}><IconTrash /></button>
            </div>
          </div>
        ))}
      </div>

      {/* ── MODALE ENRICHIE ──────────────────────────────────────── */}
      {showModal && (
        <div style={{
          position: "fixed", inset: 0,
          background: "rgba(15,23,42,0.55)", backdropFilter: "blur(4px)",
          zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center",
        }}>
          <div style={{
            background: "var(--card)", borderRadius: 16,
            width: 580, maxWidth: "92vw", maxHeight: "90vh",
            boxShadow: "0 24px 64px rgba(0,0,0,0.2)",
            border: "1px solid var(--border)",
            display: "flex", flexDirection: "column",
          }}>
            {/* Header */}
            <div style={{
              display: "flex", justifyContent: "space-between", alignItems: "center",
              padding: "20px 28px 0",
            }}>
              <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700 }}>
                {editing ? "Modifier le soignant" : "Nouveau soignant"}
              </h3>
              <button onClick={() => setShowModal(false)} style={{
                background: "none", border: "none", cursor: "pointer",
                color: "var(--muted)", padding: 4, borderRadius: 6, display: "flex",
              }}><IconClose /></button>
            </div>

            {/* Corps scrollable */}
            <div style={{ padding: "0 28px 28px", overflowY: "auto", flex: 1 }}>

              {/* ─── SECTION 1 : Infos personnelles ─────────────── */}
              <SectionTitle>👤 Informations personnelles</SectionTitle>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" }}>
                <div>
                  <label style={labelStyle}>Prénom *</label>
                  <input value={form.first_name}
                    onChange={e => setForm(p => ({ ...p, first_name: e.target.value }))}
                    style={inputStyle} placeholder="Jean" />
                </div>
                <div>
                  <label style={labelStyle}>Nom *</label>
                  <input value={form.last_name}
                    onChange={e => setForm(p => ({ ...p, last_name: e.target.value }))}
                    style={inputStyle} placeholder="Dupont" />
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" }}>
                <div>
                  <label style={labelStyle}>Email *</label>
                  <input type="email" value={form.email}
                    onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                    style={inputStyle} placeholder="jean@hopital.fr" />
                </div>
                <div>
                  <label style={labelStyle}>Téléphone</label>
                  <input value={form.phone}
                    onChange={e => setForm(p => ({ ...p, phone: e.target.value }))}
                    style={inputStyle} placeholder="06 12 34 56 78" />
                </div>
              </div>
              <label style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, cursor: "pointer", marginBottom: 4 }}>
                <input type="checkbox" checked={form.is_active}
                  onChange={e => setForm(p => ({ ...p, is_active: e.target.checked }))} />
                Soignant actif
              </label>

              {/* ─── SECTION 2 : Rôles ──────────────────────────── */}
              <SectionTitle>🏷️ Rôles</SectionTitle>
              <ChipSelect
                items={roles}
                selected={form.role_ids}
                onChange={(id) => toggleId("role_ids", id)}
              />

              {/* ─── SECTION 3 : Spécialités ────────────────────── */}
              <SectionTitle>🩺 Spécialités</SectionTitle>
              <ChipSelect
                items={specialties}
                selected={form.specialty_ids}
                onChange={(id) => toggleId("specialty_ids", id)}
              />

              {/* ─── SECTION 4 : Certifications ─────────────────── */}
              <SectionTitle>🏅 Certifications</SectionTitle>
              {certLines.map((line, i) => (
                <div key={i} style={{
                  display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto",
                  gap: 8, alignItems: "end", marginBottom: 8,
                }}>
                  <div>
                    {i === 0 && <label style={labelStyle}>Certification</label>}
                    <select value={line.certification_id}
                      onChange={e => updateCertLine(i, "certification_id", e.target.value)}
                      style={{ ...selectStyle, marginBottom: 0 }}>
                      <option value="">— Choisir —</option>
                      {certifications.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    {i === 0 && <label style={labelStyle}>Date obtention</label>}
                    <input type="date" value={line.obtained_date}
                      onChange={e => updateCertLine(i, "obtained_date", e.target.value)}
                      style={{ ...inputStyle, marginBottom: 0 }} />
                  </div>
                  <div>
                    {i === 0 && <label style={labelStyle}>Expiration</label>}
                    <input type="date" value={line.expiration_date}
                      onChange={e => updateCertLine(i, "expiration_date", e.target.value)}
                      style={{ ...inputStyle, marginBottom: 0 }} />
                  </div>
                  <button onClick={() => removeCertLine(i)} style={{
                    background: "none", border: "1px solid #fecaca", borderRadius: 8,
                    padding: "8px", color: "#ef4444", cursor: "pointer",
                    display: "flex", alignItems: "center", height: 37,
                  }}><IconTrash /></button>
                </div>
              ))}
              <button onClick={addCertLine} style={{
                background: "var(--surface)", border: "1px dashed var(--border)",
                borderRadius: 8, padding: "8px 14px", fontSize: 12,
                cursor: "pointer", color: "var(--muted)", display: "flex",
                alignItems: "center", gap: 6, width: "100%", justifyContent: "center",
              }}>
                <IconPlus /> Ajouter une certification
              </button>

              {/* ─── SECTION 5 : Contrat ────────────────────────── */}
              <SectionTitle>📋 Contrat</SectionTitle>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" }}>
                <div>
                  <label style={labelStyle}>Type de contrat</label>
                  <select value={contractForm.contract_type}
                    onChange={e => setContractForm(p => ({ ...p, contract_type: e.target.value }))}
                    style={selectStyle}>
                    <option value="">— Aucun contrat —</option>
                    {contractTypes.map(ct => (
                      <option key={ct.id} value={ct.id}>
                        {ct.name} ({ct.max_hours_per_week}h/sem{ct.night_shift_allowed ? " · nuits OK" : ""})
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Charge de travail (%)</label>
                  <input type="number" min="10" max="100" step="10"
                    value={contractForm.workload_percent}
                    onChange={e => setContractForm(p => ({ ...p, workload_percent: e.target.value }))}
                    style={inputStyle} placeholder="100" />
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 12px" }}>
                <div>
                  <label style={labelStyle}>Date de début</label>
                  <input type="date" value={contractForm.start_date}
                    onChange={e => setContractForm(p => ({ ...p, start_date: e.target.value }))}
                    style={inputStyle} />
                </div>
                <div>
                  <label style={labelStyle}>Date de fin</label>
                  <input type="date" value={contractForm.end_date}
                    onChange={e => setContractForm(p => ({ ...p, end_date: e.target.value }))}
                    style={inputStyle} />
                </div>
              </div>
            </div>

            {/* Footer */}
            <div style={{
              padding: "16px 28px", borderTop: "1px solid var(--border)",
              display: "flex", gap: 8, justifyContent: "flex-end",
            }}>
              <button onClick={() => setShowModal(false)} style={{
                background: "var(--surface)", border: "1px solid var(--border)",
                borderRadius: 8, padding: "9px 16px", fontSize: 13, cursor: "pointer",
              }}>Annuler</button>
              <button onClick={handleSave} disabled={saving} style={{
                background: "var(--accent)", color: "#fff", border: "none",
                borderRadius: 8, padding: "9px 20px", fontSize: 13,
                fontWeight: 600, cursor: "pointer",
                display: "flex", alignItems: "center", gap: 6,
                opacity: saving ? 0.7 : 1,
              }}>
                {saving && <IconSpinner />} Enregistrer
              </button>
            </div>
          </div>
        </div>
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
                {new Date(s.start_datetime).toLocaleString("fr-FR")} → {new Date(s.end_datetime).toLocaleString("fr-FR")}
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
  const [staff, setStaff]             = useState([]);
  const [shifts, setShifts]           = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading]         = useState(true);
  const [selectedStaff, setSelectedStaff]     = useState("");
  const [selectedShift, setSelectedShift]     = useState("");
  const [assigning, setAssigning]             = useState(false);
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
      if (e.status === 409 && e.payload) setConstraintError(e.payload);
      else toast(e.message, "error");
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

        {constraintError && (
          <div style={{ marginBottom: 16, padding: "12px 14px", borderRadius: 10, background: "#fef2f2", border: "1px solid #fca5a5" }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: "#9b1c1c", letterSpacing: "0.05em", marginBottom: 4 }}>
              CONTRAINTE {constraintError.code} VIOLÉE
            </div>
            <div style={{ fontSize: 13, color: "#b91c1c", lineHeight: 1.5 }}>{constraintError.detail}</div>
          </div>
        )}

        <button onClick={handleAssign} disabled={!selectedStaff || !selectedShift || assigning}
          style={{ width: "100%", background: "var(--accent)", color: "#fff", border: "none", borderRadius: 8, padding: "10px", fontSize: 13, fontWeight: 600, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", gap: 8, opacity: (!selectedStaff || !selectedShift) ? 0.5 : 1 }}>
          {assigning && <IconSpinner />} Affecter
        </button>
      </div>

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
  const [absences, setAbsences]         = useState([]);
  const [staff, setStaff]               = useState([]);
  const [absenceTypes, setAbsenceTypes] = useState([]);
  const [loading, setLoading]           = useState(true);
  const [showModal, setShowModal]       = useState(false);
  const [form, setForm]                 = useState({ staff: "", absence_type: "", start_date: "", expected_end_date: "", is_planned: true });
  const [saving, setSaving]             = useState(false);

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
          <label style={labelStyle}>Soignant</label>
          <select value={form.staff} onChange={e => setForm(p => ({ ...p, staff: e.target.value }))} style={selectStyle}>
            <option value="">— Choisir —</option>
            {staff.map(s => <option key={s.id} value={s.id}>{s.first_name} {s.last_name}</option>)}
          </select>
          <label style={labelStyle}>Type d'absence</label>
          <select value={form.absence_type} onChange={e => setForm(p => ({ ...p, absence_type: e.target.value }))} style={selectStyle}>
            <option value="">— Choisir —</option>
            {absenceTypes.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <label style={labelStyle}>Date de début</label>
          <input type="date" value={form.start_date} onChange={e => setForm(p => ({ ...p, start_date: e.target.value }))} style={inputStyle} />
          <label style={labelStyle}>Date de fin prévue</label>
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

// ─── PAGE PLANNING ────────────────────────────────────────────────────────────

function PlanningPage({ toast }) {
  const [weekOffset, setWeekOffset] = useState(0);
  const [staff,      setStaff]      = useState([]);
  const [shifts,     setShifts]     = useState([]);
  const [assigns,    setAssigns]    = useState([]);
  const [absences,   setAbsences]   = useState([]);
  const [services,   setServices]   = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [error,      setError]      = useState(null);

  // Génération automatique
  const [generating, setGenerating] = useState(false);
  const [genForm, setGenForm] = useState({
    start_date: "",
    end_date: "",
    service_id: "",
  });
  const [genResult, setGenResult] = useState(null);
  const [showScore, setShowScore] = useState(false);
  const [scoreData, setScoreData] = useState(null);

  const weekDays = useMemo(() => {
    const now    = new Date();
    const monday = new Date(now);
    monday.setDate(now.getDate() - ((now.getDay() + 6) % 7) + weekOffset * 7);
    return Array.from({ length: 7 }, (_, i) => {
      const d = new Date(monday);
      d.setDate(monday.getDate() + i);
      return d;
    });
  }, [weekOffset]);

  const fmt      = (d) => new Date(d).toISOString().slice(0, 10);
  const fmtTime  = (s) => new Date(s).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
  const fmtLabel = (d) => d.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });
  const todayStr = fmt(new Date());

  const load = useCallback(async () => {
    setLoading(true); setError(null);
    try {
      const [s, sh, a, ab, sv] = await Promise.all([
        api.staff.list(), api.shifts.list(), api.assignments.list(), api.absences.list(),
        api.services(),
      ]);
      setStaff(s); setShifts(sh); setAssigns(a); setAbsences(ab); setServices(sv);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Initialiser les dates pour la génération
  useEffect(() => {
    const monday = weekDays[0];
    const sunday = weekDays[6];
    setGenForm(prev => ({
      ...prev,
      start_date: fmt(monday),
      end_date: fmt(sunday),
    }));
  }, [weekDays]);

  const weekStart  = fmt(weekDays[0]);
  const weekEnd    = fmt(weekDays[6]);

  const weekShifts = useMemo(
    () => shifts.filter(sh => { const d = fmt(new Date(sh.start_datetime)); return d >= weekStart && d <= weekEnd; }),
    [shifts, weekStart, weekEnd]
  );

  const assignMap = useMemo(() => {
    const map = {};
    assigns.forEach(a => {
      const sh = shifts.find(s => s.id === a.shift);
      if (!sh) return;
      const d = fmt(new Date(sh.start_datetime));
      if (!map[a.staff]) map[a.staff] = {};
      if (!map[a.staff][d]) map[a.staff][d] = [];
      map[a.staff][d].push(sh);
    });
    return map;
  }, [assigns, shifts]);

  const isAbsent = (staffId, dateStr) =>
    absences.some(a => a.staff === staffId && dateStr >= a.start_date && dateStr <= a.expected_end_date);

  const dayCounts = useMemo(() =>
    weekDays.map(d => {
      const dateStr   = fmt(d);
      // Include shifts that start on this day OR end on this day (for night shifts)
      const dayShifts = weekShifts.filter(sh => {
        const startDate = fmt(new Date(sh.start_datetime));
        const endDate = fmt(new Date(sh.end_datetime));
        return startDate === dateStr || endDate === dateStr;
      });
      const filled    = assigns.filter(a => dayShifts.some(sh => sh.id === a.shift)).length;
      return { total: dayShifts.length, filled };
    }),
    [weekDays, weekShifts, assigns]
  );

  const weekLabel = `Semaine du ${weekDays[0].toLocaleDateString("fr-FR", { day: "numeric", month: "long" })} au ${weekDays[6].toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric" })}`;

  // ── Gestion génération ──────────────────────────────────────
  const handleGenerate = async () => {
    if (!genForm.start_date || !genForm.end_date) {
      toast("Veuillez sélectionner une période.", "error");
      return;
    }

    setGenerating(true);
    setGenResult(null);
    try {
      const payload = {
        start_date: genForm.start_date,
        end_date: genForm.end_date,
        save: true,
      };
      if (genForm.service_id) payload.service_id = parseInt(genForm.service_id);

      const result = await api.planning.generate(payload);
      setGenResult(result);
      load(); // Recharger les données

      const msg = `Planning généré : ${result.total_assignments} affectations` +
        (result.uncovered_shifts > 0 ? `, ${result.uncovered_shifts} postes non couverts` : "") +
        ` (score: ${result.score.toFixed(1)})`;
      toast(msg, "success");
    } catch (e) {
      toast(e.message || "Erreur lors de la génération", "error");
    } finally {
      setGenerating(false);
    }
  };

  const handleScore = async () => {
    if (!genForm.start_date || !genForm.end_date) {
      toast("Veuillez sélectionner une période.", "error");
      return;
    }

    try {
      const params = { start_date: genForm.start_date, end_date: genForm.end_date };
      if (genForm.service_id) params.service_id = genForm.service_id;

      const result = await api.planning.score(params);
      setScoreData(result);
      setShowScore(true);
    } catch (e) {
      toast(e.message || "Erreur lors du calcul du score", "error");
    }
  };

  if (loading) return <LoadingState />;
  if (error)   return <ErrorState message={error} onRetry={load} />;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, flexWrap: "wrap", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 800 }}>Planning</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "var(--muted)" }}>{weekLabel}</p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <button onClick={() => setWeekOffset(o => o - 1)} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "7px 14px", fontSize: 13, cursor: "pointer" }}>← Préc.</button>
          <button onClick={() => setWeekOffset(0)}
            style={{ background: weekOffset === 0 ? "var(--accent-soft)" : "var(--surface)", color: weekOffset === 0 ? "var(--accent)" : "var(--text)", border: "1px solid var(--border)", borderRadius: 8, padding: "7px 14px", fontSize: 13, cursor: "pointer", fontWeight: weekOffset === 0 ? 600 : 400 }}>
            Aujourd'hui
          </button>
          <button onClick={() => setWeekOffset(o => o + 1)} style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "7px 14px", fontSize: 13, cursor: "pointer" }}>Suiv. →</button>
          <button onClick={load} title="Rafraîchir" style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "7px 12px", fontSize: 14, cursor: "pointer", color: "var(--muted)" }}>↻</button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 16, marginBottom: 16, flexWrap: "wrap" }}>
        {[
          { label: "Garde de jour", bg: "#dbeafe", color: "#1e40af" },
          { label: "Garde de nuit", bg: "#ede9fe", color: "#5b21b6" },
          { label: "Absent",        bg: "#fee2e2", color: "#991b1b" },
        ].map(({ label, bg, color }) => (
          <span key={label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "var(--muted)" }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: bg, border: `1px solid ${color}55`, display: "inline-block" }} />
            {label}
          </span>
        ))}
      </div>

      {/* ─── PANNEAU DE GÉNÉRATION ─────────────────────────────── */}
      <div style={{
        background: "var(--card)", border: "1px solid var(--border)",
        borderRadius: 16, padding: 24, marginBottom: 24,
      }}>
        <h3 style={{ margin: "0 0 16px", fontSize: 15, fontWeight: 700 }}>
          ⚡ Génération automatique du planning
        </h3>
        <p style={{ margin: "0 0 16px", fontSize: 13, color: "var(--muted)", lineHeight: 1.6 }}>
          Génère un planning admissible (contraintes dures respectées) en optimisant les contraintes molles
          (équité, préférences, nuits consécutives, continuité des soins…).
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 12, alignItems: "end" }}>
          <div>
            <label style={labelStyle}>Date de début</label>
            <input
              type="date"
              value={genForm.start_date}
              onChange={e => setGenForm(p => ({ ...p, start_date: e.target.value }))}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Date de fin</label>
            <input
              type="date"
              value={genForm.end_date}
              onChange={e => setGenForm(p => ({ ...p, end_date: e.target.value }))}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle}>Service (optionnel)</label>
            <select
              value={genForm.service_id}
              onChange={e => setGenForm(p => ({ ...p, service_id: e.target.value }))}
              style={selectStyle}
            >
              <option value="">Tous les services</option>
              {services.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              onClick={handleGenerate}
              disabled={generating}
              style={{
                background: "var(--accent)", color: "#fff", border: "none",
                borderRadius: 8, padding: "9px 20px", fontSize: 13,
                fontWeight: 600, cursor: generating ? "not-allowed" : "pointer",
                display: "flex", alignItems: "center", gap: 6,
                opacity: generating ? 0.7 : 1,
                whiteSpace: "nowrap",
              }}
            >
              {generating && <IconSpinner />}
              Générer
            </button>
            <button
              onClick={handleScore}
              style={{
                background: "var(--surface)", color: "var(--text)",
                border: "1px solid var(--border)", borderRadius: 8,
                padding: "9px 16px", fontSize: 13, fontWeight: 500,
                cursor: "pointer",
              }}
            >
              Voir score
            </button>
          </div>
        </div>

        {/* Résultat de génération */}
        {genResult && (
          <div style={{
            marginTop: 20, padding: 16, borderRadius: 10,
            background: genResult.success ? "#eff6ff" : "#fef2f2",
            border: `1px solid ${genResult.success ? "#bfdbfe" : "#fecaca"}`,
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8, color: genResult.success ? "#1e40af" : "#991b1b" }}>
              {genResult.success ? "✅ Génération terminée" : "⚠️ Génération partiellement réussie"}
            </div>
            <div style={{ fontSize: 12, color: "var(--muted)", display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px" }}>
              <div>📋 Affectations créées : <strong>{genResult.total_assignments}</strong></div>
              <div>💾 Sauvegardées : <strong>{genResult.saved_count}</strong></div>
              <div>🎯 Score global : <strong>{genResult.score.toFixed(1)}</strong></div>
              <div>⚠️ Postes non couverts : <strong>{genResult.uncovered_shifts}</strong></div>
            </div>
            {genResult.uncovered.length > 0 && (
              <div style={{ marginTop: 12, fontSize: 12, color: "#991b1b" }}>
                <details>
                  <summary style={{ cursor: "pointer", fontWeight: 600 }}>Détail des postes non couverts ({genResult.uncovered.length})</summary>
                  <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                    {genResult.uncovered.slice(0, 5).map((u, i) => (
                      <li key={i}>{u.shift_label} — {u.reason}</li>
                    ))}
                    {genResult.uncovered.length > 5 && (
                      <li>… et {genResult.uncovered.length - 5} autres</li>
                    )}
                  </ul>
                </details>
              </div>
            )}
            <div style={{ marginTop: 12, fontSize: 12, color: "var(--muted)" }}>
              <details>
                <summary style={{ cursor: "pointer", fontWeight: 600 }}>Détail des pénalités (contraintes molles)</summary>
                <div style={{ marginTop: 8, display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 16px", fontSize: 11 }}>
                  <div>Nuits consécutives : <strong>{genResult.score_details.consecutive_nights?.toFixed(1)}</strong></div>
                  <div>Préférences : <strong>{genResult.score_details.preferences?.toFixed(1)}</strong></div>
                  <div>Équilibre charge : <strong>{genResult.score_details.workload_balance?.toFixed(1)}</strong></div>
                  <div>Changements service : <strong>{genResult.score_details.service_changes?.toFixed(1)}</strong></div>
                  <div>Équité week-end : <strong>{genResult.score_details.weekend_equity?.toFixed(1)}</strong></div>
                  <div>Période adaptation : <strong>{genResult.score_details.adaptation_period?.toFixed(1)}</strong></div>
                  <div>Continuité soins : <strong>{genResult.score_details.continuity?.toFixed(1)}</strong></div>
                </div>
              </details>
            </div>
          </div>
        )}
      </div>

      {/* ─── MODALE SCORE ───────────────────────────────────────── */}
      {showScore && scoreData && (
        <Modal title="Score du planning" onClose={() => setShowScore(false)}>
          <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 16 }}>
            Période : {scoreData.period.start_date} → {scoreData.period.end_date}
          </div>
          <div style={{ display: "grid", gap: 12, marginBottom: 16 }}>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: "var(--surface)", borderRadius: 8 }}>
              <span>Postes à couvrir</span>
              <strong>{scoreData.total_shifts}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: "var(--surface)", borderRadius: 8 }}>
              <span>Affectations existantes</span>
              <strong>{scoreData.total_assignments}</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: "var(--surface)", borderRadius: 8 }}>
              <span>Taux de couverture</span>
              <strong>{scoreData.coverage_rate?.toFixed(1)}%</strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 12px", background: scoreData.score < 50 ? "#eff6ff" : "#fef2f2", borderRadius: 8, border: `1px solid ${scoreData.score < 50 ? "#bfdbfe" : "#fecaca"}` }}>
              <span style={{ fontWeight: 600 }}>Score global (pénalités)</span>
              <strong style={{ color: scoreData.score < 50 ? "#1e40af" : "#991b1b" }}>{scoreData.score.toFixed(1)}</strong>
            </div>
          </div>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 8, color: "var(--muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>
            Détail des pénalités
          </div>
          <div style={{ display: "grid", gap: 6 }}>
            {Object.entries(scoreData.score_details).map(([key, value]) => (
              <div key={key} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, padding: "6px 10px", background: "var(--surface)", borderRadius: 6 }}>
                <span style={{ textTransform: "capitalize" }}>
                  {key.replace(/_/g, " ")}
                </span>
                <strong>{value?.toFixed(1)}</strong>
              </div>
            ))}
          </div>
        </Modal>
      )}

      {staff.length === 0 ? (
        <div style={{ textAlign: "center", padding: "60px 0", color: "var(--muted)", fontSize: 14 }}>Aucun soignant enregistré.</div>
      ) : (
        <div style={{ overflowX: "auto", borderRadius: 12, border: "1px solid var(--border)" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 700 }}>
            <thead>
              <tr>
                <th style={{ textAlign: "left", padding: "10px 14px", background: "var(--surface)", borderBottom: "1px solid var(--border)", fontSize: 12, fontWeight: 600, color: "var(--muted)", whiteSpace: "nowrap" }}>
                  Soignant
                </th>
                {weekDays.map(d => {
                  const isToday = fmt(d) === todayStr;
                  return (
                    <th key={fmt(d)} style={{ textAlign: "center", padding: "8px 6px", borderBottom: "1px solid var(--border)", minWidth: 100, background: isToday ? "#eff6ff" : "var(--surface)", fontSize: 12, fontWeight: isToday ? 700 : 400, color: isToday ? "var(--accent)" : "var(--muted)", whiteSpace: "nowrap" }}>
                      {fmtLabel(d)}
                    </th>
                  );
                })}
              </tr>
            </thead>

            <tbody>
              {staff.map((s, idx) => (
                <tr key={s.id}>
                  <td style={{ padding: "10px 14px", borderBottom: "1px solid var(--border)", background: idx % 2 === 0 ? "var(--card)" : "var(--surface)", whiteSpace: "nowrap" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <div style={{ width: 30, height: 30, borderRadius: "50%", background: s.is_active ? "var(--accent-soft)" : "#f1f5f9", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 700, color: "var(--accent)", flexShrink: 0 }}>
                        {s.first_name[0]}{s.last_name[0]}
                      </div>
                      <div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text)" }}>{s.first_name} {s.last_name}</div>
                        <div style={{ fontSize: 11, color: "var(--muted)" }}>{(s.roles || []).join(", ") || "—"}</div>
                      </div>
                    </div>
                  </td>

                  {weekDays.map(d => {
                    const dateStr   = fmt(d);
                    const isToday   = dateStr === todayStr;
                    const absent    = isAbsent(s.id, dateStr);
                    const dayShifts = (assignMap[s.id] || {})[dateStr] || [];

                    return (
                      <td key={dateStr} style={{ padding: 6, borderBottom: "1px solid var(--border)", textAlign: "center", verticalAlign: "top", background: isToday ? "#eff6ff" : idx % 2 === 0 ? "var(--card)" : "var(--surface)" }}>
                        {absent ? (
                          <span style={{ fontSize: 11, background: "#fee2e2", color: "#991b1b", borderRadius: 6, padding: "2px 7px", fontWeight: 600 }}>Absent</span>
                        ) : dayShifts.length === 0 ? (
                          <span style={{ fontSize: 13, color: "var(--border)" }}>—</span>
                        ) : (
                          dayShifts.map((sh, i) => {
                            const isNight = sh.shift_type_name?.toLowerCase().includes("nuit");
                            return (
                              <div key={i} style={{ background: isNight ? "#ede9fe" : "#dbeafe", color: isNight ? "#5b21b6" : "#1e40af", borderRadius: 8, padding: "4px 7px", marginBottom: 3, fontSize: 11, fontWeight: 600, textAlign: "left", lineHeight: 1.4 }}>
                                {sh.care_unit_name}
                                <br />
                                <span style={{ fontWeight: 400, fontSize: 10 }}>{fmtTime(sh.start_datetime)}–{fmtTime(sh.end_datetime)}</span>
                              </div>
                            );
                          })
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>

            <tfoot>
              <tr>
                <td style={{ padding: "8px 14px", fontSize: 11, color: "var(--muted)", borderTop: "1px solid var(--border)", background: "var(--surface)", fontWeight: 600 }}>
                  Postes / jour
                </td>
                {dayCounts.map((c, i) => (
                  <td key={i} style={{ textAlign: "center", padding: "8px 6px", fontSize: 11, borderTop: "1px solid var(--border)", background: "var(--surface)" }}>
                    {c.total > 0 ? (
                      <span style={{ color: c.filled >= c.total ? "#065f46" : c.filled > 0 ? "#92400e" : "var(--muted)", fontWeight: 600 }}>
                        {c.filled}/{c.total}
                      </span>
                    ) : "—"}
                  </td>
                ))}
              </tr>
            </tfoot>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── APP ──────────────────────────────────────────────────────────────────────

export default function App() {
  const [page, setPage]         = useState("staff");
  const [toastMsg, setToastMsg] = useState(null);

  const toast = useCallback((message, type) => setToastMsg({ message, type }), []);

  // Récupérer le cookie CSRF au montage
  useEffect(() => { api.csrf().catch(() => {}); }, []);

  const nav = [
    { id: "staff",       label: "Soignants",   icon: <IconUser /> },
    { id: "shifts",      label: "Postes",       icon: <IconShift /> },
    { id: "assignments", label: "Affectations", icon: <IconLink /> },
    { id: "absences",    label: "Absences",     icon: <IconAbsence /> },
    { id: "planning",    label: "Planning",     icon: <IconCalendar /> },
  ];

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@400;500;600&display=swap');
        @keyframes spin { to { transform: rotate(360deg); } }
        *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
        :root {
          --bg: #f8fafc; --card: #ffffff; --surface: #f1f5f9;
          --border: #e2e8f0; --text: #0f172a; --muted: #64748b;
          --accent: #2563eb; --accent-soft: #eff6ff; --nav-w: 220px;
        }
        body { font-family: 'DM Sans', sans-serif; background: var(--bg); color: var(--text); }
        h1,h2,h3,h4 { font-family: 'Syne', sans-serif; }
        select, input, button { font-family: inherit; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 99px; }
      `}</style>

      <div style={{ display: "flex", minHeight: "100vh" }}>
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

        <main style={{ flex: 1, padding: 32, overflowY: "auto" }}>
          {page === "staff"       && <StaffPage toast={toast} />}
          {page === "shifts"      && <ShiftsPage toast={toast} />}
          {page === "assignments" && <AssignmentsPage toast={toast} />}
          {page === "absences"    && <AbsencesPage toast={toast} />}
          {page === "planning"    && <PlanningPage toast={toast} />}
        </main>
      </div>

      {toastMsg && <Toast message={toastMsg.message} type={toastMsg.type} onClose={() => setToastMsg(null)} />}
    </>
  );
}