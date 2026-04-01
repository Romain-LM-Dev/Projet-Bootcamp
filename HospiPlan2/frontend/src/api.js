import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const endpoints = {
  staff: `${API_BASE}/staff/`,
  roles: `${API_BASE}/roles/`,
  specialties: `${API_BASE}/specialties/`,
  certifications: `${API_BASE}/certifications/`,
  contractTypes: `${API_BASE}/contract-types/`,
  contracts: `${API_BASE}/contracts/`,
  shifts: `${API_BASE}/shifts/`,
  shiftTemplates: `${API_BASE}/shift-templates/`,
  absences: `${API_BASE}/absences/`,
  preferences: `${API_BASE}/preferences/`,
  assignments: `${API_BASE}/assignments/`,
  planningSnapshots: `${API_BASE}/planning-snapshots/`,
  services: `${API_BASE}/services/`,
  careUnits: `${API_BASE}/care-units/`,
  shiftTypes: `${API_BASE}/shift-types/`,
  absenceTypes: `${API_BASE}/absence-types/`,
  generate: `${API_BASE}/generate/`,
};

export default api;