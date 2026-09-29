import { useCallback, useEffect, useRef, useState } from 'react';
import Card from '../components/ui/Card';
import StatCard from '../components/ui/StatCard';
import ConfirmDialog from '../components/ui/ConfirmDialog';
import { Badge } from '../components/ui/Badge';
import { LoadingState } from '../components/ui/States';
import { useActiveSession } from '../hooks/useActiveSession';
import { keystrokeApi } from '../services/endpoints';
import { classifyKey, CATEGORY_LABELS } from '../utils/keystroke';
import { formatDuration } from '../utils/format';

// ---------------------------------------------------------------------------
// Virtual Keylogger Lab
//
// SAFETY MODEL:
//  * Capture is bound ONLY to the <textarea> in this component.
//  * It runs ONLY between START TEST and STOP TEST (user-initiated).
//  * Only key metadata (category, timing) is recorded — never the characters.
//  * A persistent banner makes the active state unmistakable.
// ---------------------------------------------------------------------------

const FLUSH_INTERVAL_MS = 1500;

export default function KeyloggerLabPage() {
  const { sessions, activeId, startSession, loading } = useActiveSession();

  const [testing, setTesting] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [count, setCount] = useState(0);
  const [lastCategory, setLastCategory] = useState('—');
  const [avgInterval, setAvgInterval] = useState(0);
  const [confirmClear, setConfirmClear] = useState(false);
  const [status, setStatus] = useState('');

  // Refs holding capture state that must not trigger re-renders per keypress.
  const bufferRef = useRef([]); // pending events not yet sent
  const seqRef = useRef(0);
  const lastTsRef = useRef(null);
  const keyDownTimes = useRef({});
  const intervalsRef = useRef([]);
  const startTimeRef = useRef(null);
  const sessionRef = useRef(null);
  const textareaRef = useRef(null);

  sessionRef.current = activeId;

  // Timer tick.
  useEffect(() => {
    if (!testing) return;
    const id = setInterval(() => {
      setElapsed((Date.now() - startTimeRef.current) / 1000);
    }, 250);
    return () => clearInterval(id);
  }, [testing]);

  const flush = useCallback(async () => {
    if (!sessionRef.current || bufferRef.current.length === 0) return;
    const batch = bufferRef.current;
    bufferRef.current = [];
    try {
      await keystrokeApi.sendEvents(sessionRef.current, batch);
    } catch {
      // Re-queue on failure so nothing is lost.
      bufferRef.current = [...batch, ...bufferRef.current];
      setStatus('Network issue — retrying…');
    }
  }, []);

  // Periodic flush while testing.
  useEffect(() => {
    if (!testing) return;
    const id = setInterval(flush, FLUSH_INTERVAL_MS);
    return () => clearInterval(id);
  }, [testing, flush]);

  const kpm = elapsed > 0 ? (count / elapsed) * 60 : 0;

  async function handleStart() {
    let sid = activeId;
    // If no active session exists, create one automatically for the test.
    const current = sessions.find((s) => s.id === activeId);
    if (!sid || current?.status !== 'ACTIVE') {
      const s = await startSession('Keylogger Lab test');
      sid = s.id;
    }
    seqRef.current = 0;
    lastTsRef.current = null;
    intervalsRef.current = [];
    keyDownTimes.current = {};
    bufferRef.current = [];
    startTimeRef.current = Date.now();
    setCount(0);
    setElapsed(0);
    setAvgInterval(0);
    setLastCategory('—');
    setStatus('');
    setTesting(true);
    setTimeout(() => textareaRef.current?.focus(), 50);
  }

  async function handleStop() {
    setTesting(false);
    await flush();
    setStatus('Test stopped. Metadata saved.');
  }

  function handleClear() {
    setConfirmClear(false);
    bufferRef.current = [];
    seqRef.current = 0;
    lastTsRef.current = null;
    intervalsRef.current = [];
    setCount(0);
    setElapsed(0);
    setAvgInterval(0);
    setLastCategory('—');
    startTimeRef.current = Date.now();
    setStatus('Local session counters cleared.');
  }

  function onKeyDown(e) {
    if (!testing) return;
    // Record keydown time for duration calc (control keys use event.key).
    keyDownTimes.current[e.code] = performance.now();
  }

  function onKeyUp(e) {
    if (!testing) return;
    const now = performance.now();
    const { category, label } = classifyKey(e);

    // Inter-key interval.
    let interval = null;
    if (lastTsRef.current != null) {
      interval = now - lastTsRef.current;
      intervalsRef.current.push(interval);
    }
    lastTsRef.current = now;

    // Hold duration when we saw the matching keydown.
    const down = keyDownTimes.current[e.code];
    const duration = down != null ? now - down : null;
    delete keyDownTimes.current[e.code];

    bufferRef.current.push({
      sequence_number: seqRef.current++,
      category,
      key_label: label,
      interval_ms: interval,
      duration_ms: duration,
      client_timestamp_ms: now,
    });

    setCount((c) => c + 1);
    setLastCategory(CATEGORY_LABELS[category] || category);
    const arr = intervalsRef.current;
    if (arr.length) setAvgInterval(arr.reduce((a, b) => a + b, 0) / arr.length);
  }

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Virtual Keylogger Lab</h1>
          <p className="text-sm text-slate-400">
            Analyze your own typing behavior inside this sandboxed test area.
          </p>
        </div>
        {activeId && <Badge tone="accent">Session #{activeId}</Badge>}
      </div>

      {/* Prominent active-state banner (safety requirement). */}
      <div
        className={`rounded-xl border p-4 text-sm font-medium transition-colors ${
          testing
            ? 'border-risk-critical/50 bg-risk-critical/10 text-risk-critical'
            : 'border-base-700 bg-base-900 text-slate-400'
        }`}
      >
        {testing ? (
          <span className="flex items-center gap-2">
            <span className="inline-block h-2.5 w-2.5 animate-pulse rounded-full bg-risk-critical" />
            TEST MODE — Input is being analyzed only inside this application. No
            characters are stored; only key category + timing metadata.
          </span>
        ) : (
          'TEST MODE INACTIVE — Press START TEST to begin capturing keystroke metadata in the box below.'
        )}
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Session timer" value={formatDuration(elapsed)} icon="⏱️" />
        <StatCard label="Total keystrokes" value={count} icon="⌨️" accent="text-slate-100" />
        <StatCard
          label="Keystrokes / min"
          value={kpm.toFixed(0)}
          icon="⚡"
          accent="text-accent"
        />
        <StatCard
          label="Avg interval"
          value={`${avgInterval.toFixed(0)} ms`}
          icon="📏"
          accent="text-slate-100"
        />
      </div>

      <Card
        title="Test input area"
        subtitle="Type here while a test is active. Only metadata leaves this box."
        actions={
          <div className="flex gap-2">
            {!testing ? (
              <button className="btn-primary" onClick={handleStart}>
                ▶ Start test
              </button>
            ) : (
              <button className="btn-danger" onClick={handleStop}>
                ■ Stop test
              </button>
            )}
            <button
              className="btn-ghost"
              onClick={() => setConfirmClear(true)}
              disabled={testing}
            >
              Clear session
            </button>
          </div>
        }
      >
        <textarea
          ref={textareaRef}
          className="input h-44 font-mono resize-none disabled:opacity-60"
          placeholder={
            testing
              ? 'Start typing — your keystroke behavior is being analyzed…'
              : 'Press "Start test" to enable capture.'
          }
          disabled={!testing}
          onKeyDown={onKeyDown}
          onKeyUp={onKeyUp}
        />
        <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-1 text-xs text-slate-400">
          <span>
            Last key category:{' '}
            <span className="text-slate-200 font-medium">{lastCategory}</span>
          </span>
          <span>
            Pending buffer:{' '}
            <span className="text-slate-200 font-medium">
              {bufferRef.current.length}
            </span>
          </span>
          {status && <span className="text-accent">{status}</span>}
        </div>
      </Card>

      <Card title="How this stays safe">
        <ul className="list-disc pl-5 text-sm text-slate-400 space-y-1">
          <li>Capture is bound only to the textarea above — never the OS or other apps.</li>
          <li>It runs only between Start and Stop, which you control.</li>
          <li>Only key <em>category</em> and timing are recorded — not the characters typed.</li>
          <li>Control-key labels (Enter, Shift…) are whitelisted; letters/digits are never labeled.</li>
        </ul>
      </Card>

      <ConfirmDialog
        open={confirmClear}
        title="Clear session counters?"
        message="This resets the local timer and counters for a fresh measurement. Already-saved metadata on the server is not deleted."
        confirmLabel="Clear"
        onConfirm={handleClear}
        onCancel={() => setConfirmClear(false)}
      />
    </div>
  );
}
