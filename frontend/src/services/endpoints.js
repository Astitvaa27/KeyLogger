import api from './api';

// ---- Auth ----
export const authApi = {
  register: (data) => api.post('/auth/register', data).then((r) => r.data),
  login: (data) => api.post('/auth/login', data).then((r) => r.data),
  me: () => api.get('/auth/me').then((r) => r.data),
  logout: () => api.post('/auth/logout').then((r) => r.data),
};

// ---- Sessions ----
export const sessionApi = {
  start: (label) => api.post('/sessions/start', { label }).then((r) => r.data),
  stop: (sessionId) =>
    api.post(`/sessions/stop?session_id=${sessionId}`).then((r) => r.data),
  list: () => api.get('/sessions').then((r) => r.data),
  get: (id) => api.get(`/sessions/${id}`).then((r) => r.data),
};

// ---- Keystrokes ----
export const keystrokeApi = {
  sendEvents: (sessionId, events) =>
    api.post('/keystrokes/events', { session_id: sessionId, events }).then((r) => r.data),
  statistics: (sessionId) =>
    api.get(`/keystrokes/statistics?session_id=${sessionId}`).then((r) => r.data),
};

// ---- Simulation ----
export const simulationApi = {
  start: (sessionId, profile = 'balanced') =>
    api.post('/simulation/start', { session_id: sessionId, profile }).then((r) => r.data),
  generate: (sessionId, count = 1, profile = 'balanced') =>
    api
      .post('/simulation/generate', { session_id: sessionId, count, profile })
      .then((r) => r.data),
  stop: (sessionId) =>
    api.post('/simulation/stop', { session_id: sessionId }).then((r) => r.data),
  reset: (sessionId) =>
    api.post('/simulation/reset', { session_id: sessionId }).then((r) => r.data),
  events: (sessionId) =>
    api.get(`/simulation/events?session_id=${sessionId}`).then((r) => r.data),
};

// ---- Detection ----
export const detectionApi = {
  rules: () => api.get('/detection/rules').then((r) => r.data),
  analyze: (sessionId) =>
    api.post('/detection/analyze', { session_id: sessionId }).then((r) => r.data),
  results: (sessionId) =>
    api.get(`/detection/results?session_id=${sessionId}`).then((r) => r.data),
};

// ---- Dashboard ----
export const dashboardApi = {
  summary: () => api.get('/dashboard/summary').then((r) => r.data),
};
