/**
 * api.js — Couche de communication avec le backend Django
 * Toutes les fonctions retournent la réponse JSON ou lèvent une Error.
 */

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000/api";

async function request(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  };
  if (body !== null) opts.body = JSON.stringify(body);

  const res = await fetch(`${BASE_URL}${path}`, opts);

  if (res.status === 204) return null; // No Content

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    // On préserve le payload pour que l'UI puisse afficher le code de contrainte
    const err = new Error(data.detail ?? `Erreur HTTP ${res.status}`);
    err.status = res.status;
    err.payload = data;
    throw err;
  }
  return data;
}

// ── Soignants ─────────────────────────────────────────────────────────────────
export const api = {
  staff: {
    list: ()               => request("GET", "/staff/"),
    get:  (id)             => request("GET", `/staff/${id}/`),
    create: (data)         => request("POST", "/staff/", data),
    update: (id, data)     => request("PUT", `/staff/${id}/`, data),
    patch:  (id, data)     => request("PATCH", `/staff/${id}/`, data),
    delete: (id)           => request("DELETE", `/staff/${id}/`),
  },

  // ── Postes de garde ─────────────────────────────────────────────────────────
  shifts: {
    list:   ()             => request("GET", "/shifts/"),
    get:    (id)           => request("GET", `/shifts/${id}/`),
    create: (data)         => request("POST", "/shifts/", data),
    update: (id, data)     => request("PUT", `/shifts/${id}/`, data),
    delete: (id)           => request("DELETE", `/shifts/${id}/`),
  },

  // ── Affectations (POST peut retourner 409 avec code contrainte) ──────────────
  assignments: {
    list:   ()             => request("GET", "/assignments/"),
    create: (staffId, shiftId) =>
      request("POST", "/assignments/", { staff_id: staffId, shift_id: shiftId }),
    delete: (id)           => request("DELETE", `/assignments/${id}/`),
  },

  // ── Absences ────────────────────────────────────────────────────────────────
  absences: {
    list:    (staffId)     => request("GET", staffId ? `/absences/?staff_id=${staffId}` : "/absences/"),
    create:  (data)        => request("POST", "/absences/", data),
    delete:  (id)          => request("DELETE", `/absences/${id}/`),
  },

  // ── Référentiels ────────────────────────────────────────────────────────────
  certifications: () => request("GET", "/certifications/"),
  contractTypes:  () => request("GET", "/contract-types/"),
  shiftTypes:     () => request("GET", "/shift-types/"),
  absenceTypes:   () => request("GET", "/absence-types/"),
  services:       () => request("GET", "/services/"),
};
