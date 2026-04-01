const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
  return null;
}

async function request(endpoint, { method = "GET", body } = {}) {
  const headers = { "Content-Type": "application/json" };

  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    const token = getCookie("csrftoken");
    if (token) headers["X-CSRFToken"] = token;
  }

  const res = await fetch(`${BASE}${endpoint}`, {
    method,
    headers,
    credentials: "include",
    ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
  });

  if (!res.ok) {
    const payload = await res.json().catch(() => null);
    const err = new Error(
      payload?.detail ||
        (typeof payload === "object" ? JSON.stringify(payload) : `Erreur ${res.status}`)
    );
    err.status = res.status;
    err.payload = payload;
    throw err;
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  csrf: () => fetch(`${BASE}/csrf/`, { credentials: "include" }),

  staff: {
    list:   ()         => request("/staff/"),
    get:    (id)       => request(`/staff/${id}/`),
    create: (data)     => request("/staff/",       { method: "POST",  body: data }),
    update: (id, data) => request(`/staff/${id}/`, { method: "PATCH", body: data }),
    delete: (id)       => request(`/staff/${id}/`, { method: "DELETE" }),
  },

  shifts: {
    list:   ()   => request("/shifts/"),
    delete: (id) => request(`/shifts/${id}/`, { method: "DELETE" }),
  },

  assignments: {
    list:   ()             => request("/assignments/"),
    create: (staff, shift) => request("/assignments/", { method: "POST", body: { staff, shift } }),
    delete: (id)           => request(`/assignments/${id}/`, { method: "DELETE" }),
  },

  absences: {
    list:   ()     => request("/absences/"),
    create: (data) => request("/absences/", { method: "POST", body: data }),
    delete: (id)   => request(`/absences/${id}/`, { method: "DELETE" }),
  },

  absenceTypes:   () => request("/absence-types/"),
  roles:          () => request("/roles/"),
  specialties:    () => request("/specialties/"),
  certifications: () => request("/certifications/"),
  contractTypes:  () => request("/contract-types/"),

  staffCertifications: {
    list:   (staffId) => request(`/staff-certifications/?staff=${staffId}`),
    create: (data)    => request("/staff-certifications/", { method: "POST",   body: data }),
    delete: (id)      => request(`/staff-certifications/${id}/`, { method: "DELETE" }),
  },

  contracts: {
    list:   (staffId) => request(`/contracts/?staff=${staffId}`),
    create: (data)    => request("/contracts/",       { method: "POST",  body: data }),
    update: (id, data) => request(`/contracts/${id}/`, { method: "PATCH", body: data }),
    delete: (id)      => request(`/contracts/${id}/`, { method: "DELETE" }),
  },
};