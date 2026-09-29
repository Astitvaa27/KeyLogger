import { useCallback, useEffect, useState } from 'react';
import { sessionApi } from '../services/endpoints';

const KEY = 'keylogger.activeSessionId';

// Shared helper for tracking the "current working session" across pages.
// Persists the chosen session id in localStorage so the Lab, Simulation, and
// Detection pages all operate on the same session.
export function useActiveSession() {
  const [sessions, setSessions] = useState([]);
  const [activeId, setActiveId] = useState(() => {
    const v = localStorage.getItem(KEY);
    return v ? Number(v) : null;
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await sessionApi.list();
      setSessions(list);
      // Keep a valid active id.
      setActiveId((cur) => {
        if (cur && list.some((s) => s.id === cur)) return cur;
        const firstActive = list.find((s) => s.status === 'ACTIVE');
        const fallback = firstActive?.id ?? list[0]?.id ?? null;
        if (fallback) localStorage.setItem(KEY, String(fallback));
        return fallback;
      });
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const selectSession = useCallback((id) => {
    setActiveId(id);
    if (id) localStorage.setItem(KEY, String(id));
    else localStorage.removeItem(KEY);
  }, []);

  const startSession = useCallback(
    async (label) => {
      const s = await sessionApi.start(label);
      await refresh();
      selectSession(s.id);
      return s;
    },
    [refresh, selectSession],
  );

  const stopSession = useCallback(
    async (id) => {
      const s = await sessionApi.stop(id);
      await refresh();
      return s;
    },
    [refresh],
  );

  const activeSession = sessions.find((s) => s.id === activeId) || null;

  return {
    sessions,
    activeId,
    activeSession,
    loading,
    error,
    refresh,
    selectSession,
    startSession,
    stopSession,
  };
}
