import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const endpoints = {
  authLogin: '/auth/login/',
  authLogout: '/auth/logout/',
  authUser: '/auth/user/',
  staff: '/staff/',
  roles: '/roles/',
  staffRoles: '/staff-roles/',
  specialties: '/specialties/',
  certifications: '/certifications/',
  contractTypes: '/contract-types/',
  contracts: '/contracts/',
  shifts: '/shifts/',
  shiftTemplates: '/shift-templates/',
  absences: '/absences/',
  preferences: '/preferences/',
  assignments: '/assignments/',
  planningSnapshots: '/planning-snapshots/',
  optimizationRuns: '/optimization-runs/',
  services: '/services/',
  careUnits: '/care-units/',
  shiftTypes: '/shift-types/',
  absenceTypes: '/absence-types/',
  generate: '/generate/',
};

export default api;
