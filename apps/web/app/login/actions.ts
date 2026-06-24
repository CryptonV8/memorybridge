'use server';

import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';
import { headers } from 'next/headers';

// ── In-memory login rate limiter ──────────────────────────────────────────────
// DEMO-ONLY: single-instance in-memory store. Not suitable for multi-replica
// deployments — use a shared distributed store (e.g. Upstash Redis) in production.
// Limit: 5 login attempts per 60 seconds per IP address.
const LOGIN_RATE_LIMIT_WINDOW_MS = 60 * 1000;
const LOGIN_RATE_LIMIT_MAX = 5;
const loginAttempts = new Map<string, number[]>();

function checkLoginRateLimit(ip: string): boolean {
  const now = Date.now();
  const windowStart = now - LOGIN_RATE_LIMIT_WINDOW_MS;
  const attempts = (loginAttempts.get(ip) ?? []).filter(t => t > windowStart);
  if (attempts.length >= LOGIN_RATE_LIMIT_MAX) {
    return false; // rate limit exceeded
  }
  attempts.push(now);
  loginAttempts.set(ip, attempts);
  return true;
}

async function getClientIp(): Promise<string> {
  // headers() in Next.js 15 returns a Promise — must be awaited.
  const requestHeaders = await headers();
  const forwarded = requestHeaders.get('x-forwarded-for');
  if (forwarded) return forwarded.split(',')[0].trim();
  const realIp = requestHeaders.get('x-real-ip');
  if (realIp) return realIp.trim();
  return 'unknown';
}

// loginDemo uses direct form action — formData only, no useActionState required.
// Rate limit exceeded returns early (error not surfaced via form state; page reload resets).
// On success, redirect() throws a NEXT_REDIRECT — never reaches a return value.
export async function loginDemo(formData: FormData): Promise<void> {
  const ip = await getClientIp();
  if (!checkLoginRateLimit(ip)) {
    // Rate limiting: in a real app, surface this via useActionState / redirect with error query param.
    // For the demo, simply return without creating a session.
    return;
  }

  // In a real app we would check credentials. Here we just set the demo session.
  const session = await getSession();
  session.isDemoAuthenticated = true;
  await session.save();
  redirect('/caregiver'); // throws NEXT_REDIRECT — never reaches return
}


export async function logoutDemo() {
  const session = await getSession();
  session.destroy();
  redirect('/login');
}
