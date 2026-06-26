export const dynamic = 'force-dynamic';

import type { Metadata } from 'next';
import { AlertTriangle } from 'lucide-react';
import { getTodayRoutines } from '@/lib/api-client';
import { TodayClient } from './TodayClient';
import './today.css';

export const metadata: Metadata = {
  title: "Maria's Daily Routines — MemoryBridge",
  description: "Today's scheduled routines for Maria Petrova",
};

export default async function TodayPage() {
  let routines: Awaited<ReturnType<typeof getTodayRoutines>> = [];
  let fetchError: string | null = null;

  try {
    routines = await getTodayRoutines();
  } catch (err) {
    fetchError =
      err instanceof Error ? err.message : 'Could not load today\'s routines. Please try again.';
  }

  return (
    <div className="today-page-root">
      {/* Skip navigation */}
      <a
        href="#today-main"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-white text-slate-900 px-4 py-2 rounded shadow-md z-50 font-semibold text-lg"
      >
        Skip to routines
      </a>

      {/* Demo banner */}
      <div className="today-demo-banner" role="complementary" aria-label="Demo notice">
        <AlertTriangle className="today-demo-banner-icon" aria-hidden="true" />
        <span>Demo only. Synthetic data. Not a medical device.</span>
      </div>

      {/* User greeting header */}
      <header className="today-header">
        <div className="today-header-inner">
          <span className="today-header-logo" aria-hidden="true">MB</span>
          <div>
            <h2 className="today-header-name">Maria Petrova</h2>
            <p className="today-header-sub">Your daily routines</p>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main id="today-main" className="today-main" tabIndex={-1}>
        {fetchError ? (
          <div className="today-fetch-error" role="alert" aria-live="assertive">
            <p className="today-fetch-error-msg">{fetchError}</p>
            <p className="today-fetch-error-hint">
              Please ask your caregiver to check the connection.
            </p>
          </div>
        ) : (
          <TodayClient routines={routines} />
        )}
      </main>
    </div>
  );
}
