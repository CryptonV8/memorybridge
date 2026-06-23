'use client';

import { useState, useTransition, useRef, useCallback } from 'react';
import { TodayRoutine } from '@/lib/api-client';
import { markDoneAction, helpAction, contactAction } from './actions';

interface Props {
  routines: TodayRoutine[];
}

type ActionState =
  | { kind: 'idle' }
  | { kind: 'loading'; action: string }
  | { kind: 'success'; message: string }
  | { kind: 'error'; message: string };

export function TodayClient({ routines }: Props) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [actionState, setActionState] = useState<ActionState>({ kind: 'idle' });
  const [isPending, startTransition] = useTransition();
  const [isSpeaking, setIsSpeaking] = useState(false);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  const activeRoutines = routines.filter(
    (r) => r.status === 'active' || r.status === 'pending_approval'
  );

  const routine = activeRoutines[currentIndex] ?? null;
  const hasNext = currentIndex < activeRoutines.length - 1;
  const hasPrev = currentIndex > 0;

  // ── Text-to-speech ───────────────────────────────────────────────────────────
  const speak = useCallback(() => {
    if (!routine) return;
    if (typeof window === 'undefined' || !window.speechSynthesis) return;
    synthRef.current = window.speechSynthesis;
    synthRef.current.cancel();

    const text = [
      `It is time for: ${routine.title}.`,
      ...routine.steps_json,
    ].join(' ');

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.85;
    utterance.pitch = 1.0;
    utterance.lang = 'en-US';
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);
    synthRef.current.speak(utterance);
  }, [routine]);

  const stopSpeaking = useCallback(() => {
    synthRef.current?.cancel();
    setIsSpeaking(false);
  }, []);

  // ── Actions ──────────────────────────────────────────────────────────────────
  const handleDone = () => {
    if (!routine) return;
    stopSpeaking();
    setActionState({ kind: 'loading', action: 'done' });
    startTransition(async () => {
      const result = await markDoneAction(routine.id);
      if (result.error) {
        setActionState({ kind: 'error', message: result.error });
      } else {
        setActionState({ kind: 'success', message: 'Well done! This routine is marked complete.' });
      }
    });
  };

  const handleHelp = () => {
    if (!routine) return;
    stopSpeaking();
    setActionState({ kind: 'loading', action: 'help' });
    startTransition(async () => {
      const result = await helpAction(routine.id, routine.title);
      if (result.error) {
        setActionState({ kind: 'error', message: result.error });
      } else {
        setActionState({
          kind: 'success',
          message: 'Your caregiver has been notified. Help is on the way.',
        });
      }
    });
  };

  const handleContact = () => {
    stopSpeaking();
    setActionState({ kind: 'loading', action: 'contact' });
    startTransition(async () => {
      const result = await contactAction(routine?.id);
      if (result.error) {
        setActionState({ kind: 'error', message: result.error });
      } else {
        setActionState({
          kind: 'success',
          message: 'Your caregiver has been notified that you would like to speak with them.',
        });
      }
    });
  };

  const dismissState = () => setActionState({ kind: 'idle' });

  // ── Empty state ──────────────────────────────────────────────────────────────
  if (activeRoutines.length === 0) {
    return (
      <div className="today-empty" role="main" aria-label="Today's routines">
        <div className="today-empty-card">
          <span className="today-empty-icon" aria-hidden="true">✓</span>
          <h1 className="today-empty-heading">You have no routines scheduled right now.</h1>
          <p className="today-empty-body">
            Your caregiver will add new routines when needed. You are doing well.
          </p>
        </div>
      </div>
    );
  }

  // ── Success / Error overlay ───────────────────────────────────────────────────
  if (actionState.kind === 'success' || actionState.kind === 'error') {
    const isSuccess = actionState.kind === 'success';
    return (
      <div className="today-feedback" role="main" aria-live="assertive">
        <div className={`today-feedback-card ${isSuccess ? 'today-feedback-success' : 'today-feedback-error'}`}>
          <span className="today-feedback-icon" aria-hidden="true">
            {isSuccess ? '✓' : '!'}
          </span>
          <p className="today-feedback-message">{actionState.message}</p>
          <button
            id="today-feedback-dismiss"
            className="today-btn today-btn-neutral"
            onClick={dismissState}
            autoFocus
          >
            Continue
          </button>
        </div>
      </div>
    );
  }

  // ── Main routine card ────────────────────────────────────────────────────────
  const isLoading = actionState.kind === 'loading' || isPending;

  return (
    <div className="today-root" role="main" aria-label="Today's routines">
      {/* Time display */}
      <LiveClock />

      {/* Pagination indicator */}
      {activeRoutines.length > 1 && (
        <p className="today-pagination" aria-label={`Routine ${currentIndex + 1} of ${activeRoutines.length}`}>
          {currentIndex + 1} of {activeRoutines.length}
        </p>
      )}

      {/* Routine card */}
      <article
        className="today-card"
        aria-label={`Routine: ${routine.title}`}
      >
        <header className="today-card-header">
          <h1 className="today-card-title">{routine.title}</h1>
          {routine.scheduled_time && (
            <p className="today-card-time" aria-label={`Scheduled at ${routine.scheduled_time}`}>
              {routine.scheduled_time}
            </p>
          )}
        </header>

        {/* Steps */}
        <ol className="today-steps" aria-label="Steps">
          {routine.steps_json.map((step, i) => (
            <li key={i} className="today-step">
              <span className="today-step-num" aria-hidden="true">{i + 1}</span>
              <span className="today-step-text">{step}</span>
            </li>
          ))}
        </ol>

        {/* Listen button */}
        <div className="today-listen-row">
          {!isSpeaking ? (
            <button
              id="today-btn-listen"
              className="today-btn today-btn-listen"
              onClick={speak}
              disabled={isLoading}
              aria-label="Listen to this routine read aloud"
            >
              <span aria-hidden="true">▶</span> Listen
            </button>
          ) : (
            <button
              id="today-btn-stop"
              className="today-btn today-btn-listen"
              onClick={stopSpeaking}
              aria-label="Stop reading aloud"
            >
              <span aria-hidden="true">■</span> Stop
            </button>
          )}
        </div>
      </article>

      {/* Primary action buttons */}
      <div className="today-actions" aria-label="Actions">
        <button
          id="today-btn-done"
          className="today-btn today-btn-done"
          onClick={handleDone}
          disabled={isLoading}
          aria-label="Mark this routine as done"
        >
          {actionState.kind === 'loading' && actionState.action === 'done'
            ? 'Marking…'
            : 'Done'}
        </button>

        <button
          id="today-btn-help"
          className="today-btn today-btn-help"
          onClick={handleHelp}
          disabled={isLoading}
          aria-label="Request help from your caregiver"
        >
          {actionState.kind === 'loading' && actionState.action === 'help'
            ? 'Sending…'
            : 'Help me'}
        </button>

        <button
          id="today-btn-contact"
          className="today-btn today-btn-contact"
          onClick={handleContact}
          disabled={isLoading}
          aria-label="Ask your caregiver to contact you"
        >
          {actionState.kind === 'loading' && actionState.action === 'contact'
            ? 'Sending…'
            : 'Contact my caregiver'}
        </button>
      </div>

      {/* Prev / Next navigation for multiple routines */}
      {activeRoutines.length > 1 && (
        <nav className="today-nav" aria-label="Navigate between routines">
          <button
            id="today-btn-prev"
            className="today-btn today-btn-nav"
            onClick={() => { setCurrentIndex((i) => i - 1); setActionState({ kind: 'idle' }); }}
            disabled={!hasPrev || isLoading}
            aria-label="Previous routine"
          >
            ← Previous
          </button>
          <button
            id="today-btn-next"
            className="today-btn today-btn-nav"
            onClick={() => { setCurrentIndex((i) => i + 1); setActionState({ kind: 'idle' }); }}
            disabled={!hasNext || isLoading}
            aria-label="Next routine"
          >
            Next →
          </button>
        </nav>
      )}
    </div>
  );
}

// ── Live clock sub-component ──────────────────────────────────────────────────
function LiveClock() {
  const [time, setTime] = useState<string>('');

  // Format time immediately on client
  if (typeof window !== 'undefined' && !time) {
    setTime(
      new Intl.DateTimeFormat('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      }).format(new Date())
    );
  }

  return (
    <div className="today-clock" aria-label="Current date and time" aria-live="off">
      {time || '—'}
    </div>
  );
}
