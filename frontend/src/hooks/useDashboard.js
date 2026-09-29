import { useCallback, useEffect, useRef, useState } from 'react';
import { dashboardApi } from '../services/endpoints';
import { getToken, WS_BASE_URL } from '../services/api';

// Loads the dashboard summary via REST, then keeps it fresh over WebSocket.
// Falls back to periodic REST polling if the socket cannot connect.
export function useDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [live, setLive] = useState(false);
  const wsRef = useRef(null);
  const pollRef = useRef(null);

  const loadOnce = useCallback(async () => {
    try {
      setSummary(await dashboardApi.summary());
      setError(null);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOnce();

    const token = getToken();
    let closedByUs = false;

    function startPolling() {
      if (pollRef.current) return;
      pollRef.current = setInterval(loadOnce, 6000);
    }

    try {
      const ws = new WebSocket(`${WS_BASE_URL}/dashboard/ws?token=${token}`);
      wsRef.current = ws;
      ws.onopen = () => setLive(true);
      ws.onmessage = (evt) => {
        try {
          setSummary(JSON.parse(evt.data));
          setLoading(false);
        } catch {
          /* ignore malformed frame */
        }
      };
      ws.onerror = () => {
        setLive(false);
        startPolling();
      };
      ws.onclose = () => {
        setLive(false);
        if (!closedByUs) startPolling();
      };
    } catch {
      startPolling();
    }

    return () => {
      closedByUs = true;
      if (wsRef.current) wsRef.current.close();
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [loadOnce]);

  return { summary, loading, error, live, reload: loadOnce };
}
