import { z } from 'zod';
import {
  RoutineSchema,
  Routine,
  PaginatedRoutinesSchema,
  InterpretationDraftSchema,
  AlertSchema,
  Alert,
  AuditEventSchema,
  AuditEvent,
} from './api-schemas';

const API_BASE = process.env.AGENT_API_BASE_URL;
const TOKEN = process.env.DEMO_CAREGIVER_TOKEN;

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  if (!API_BASE || !TOKEN) {
    throw new Error('API configuration is missing on the server.');
  }

  const url = `${API_BASE}${endpoint}`;
  
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${TOKEN}`);
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
    cache: 'no-store', // Disable caching for demo app to avoid stale data
  });

  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function interpretRoutine(text: string, assistedUserId: string = 'user-assisted-maria') {
  const data = await fetchAPI('/api/routines/interpret', {
    method: 'POST',
    body: JSON.stringify({ text, assisted_user_id: assistedUserId }),
  });
  return InterpretationDraftSchema.parse(data);
}

export async function getRoutine(id: string): Promise<Routine> {
  const data = await fetchAPI(`/api/routines/${id}`);
  return RoutineSchema.parse(data);
}

export async function listRoutines(cursor?: string) {
  const url = cursor ? `/api/caregivers/me/routines?cursor=${cursor}` : `/api/caregivers/me/routines`;
  const data = await fetchAPI(url);
  return PaginatedRoutinesSchema.parse(data);
}

export async function updateRoutine(id: string, updates: Partial<Routine>) {
  const payload = {
    title: updates.title,
    steps_json: updates.steps_json,
    purpose: updates.purpose,
    scheduled_time: updates.scheduled_time,
    timezone: updates.timezone,
  };
  const data = await fetchAPI(`/api/routines/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
  return RoutineSchema.parse(data);
}

export async function approveRoutine(id: string) {
  const data = await fetchAPI(`/api/routines/${id}/approve`, {
    method: 'POST',
    body: JSON.stringify({ routine_id: id }),
  });
  return z.object({ status: z.string(), routine_id: z.string() }).parse(data);
}

export async function rejectRoutine(id: string) {
  const data = await fetchAPI(`/api/routines/${id}/reject`, {
    method: 'POST',
  });
  return z.object({ status: z.string(), routine_id: z.string() }).parse(data);
}

export async function getAlerts(): Promise<Alert[]> {
  const data = await fetchAPI('/api/caregivers/me/alerts');
  return z.array(AlertSchema).parse(data);
}

export async function getAuditEvents(correlationId: string): Promise<AuditEvent[]> {
  const data = await fetchAPI(`/api/audit/${correlationId}`);
  return z.array(AuditEventSchema).parse(data);
}

// ─── Assisted User API (server-side, uses DEMO_ASSISTED_USER_TOKEN) ─────────

const ASSISTED_API_BASE = process.env.AGENT_API_BASE_URL;
const ASSISTED_TOKEN = process.env.DEMO_ASSISTED_USER_TOKEN;
const ASSISTED_USER_ID = process.env.DEMO_ASSISTED_USER_ID ?? 'user-assisted-maria';

async function fetchAssistedAPI(endpoint: string, options: RequestInit = {}) {
  if (!ASSISTED_API_BASE || !ASSISTED_TOKEN) {
    throw new Error('Assisted-user API configuration is missing on the server.');
  }
  const url = `${ASSISTED_API_BASE}${endpoint}`;
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${ASSISTED_TOKEN}`);
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  const response = await fetch(url, { ...options, headers, cache: 'no-store' });
  if (!response.ok) {
    let errorDetail = 'An error occurred';
    try {
      const errorData = await response.json();
      errorDetail = errorData.detail || errorDetail;
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }
  if (response.status === 204) return null;
  return response.json();
}

export const TodayRoutineSchema = z.object({
  id: z.string(),
  title: z.string(),
  purpose: z.string().nullable().optional(),
  scheduled_time: z.string(),
  timezone: z.string().optional(),
  steps_json: z.array(z.string()),
  status: z.string(),
});

export type TodayRoutine = z.infer<typeof TodayRoutineSchema>;

export async function getTodayRoutines(): Promise<TodayRoutine[]> {
  const data = await fetchAssistedAPI(`/api/users/${ASSISTED_USER_ID}/today`);
  return z.array(TodayRoutineSchema).parse(data);
}

export async function markRoutineDone(routineId: string): Promise<void> {
  await fetchAssistedAPI(`/api/routines/${routineId}/status`, {
    method: 'POST',
    body: JSON.stringify({ status: 'completed' }),
  });
}

export async function requestHelp(routineId: string, routineTitle: string): Promise<void> {
  await fetchAssistedAPI(`/api/users/${ASSISTED_USER_ID}/help`, {
    method: 'POST',
    body: JSON.stringify({ routine_id: routineId, routine_title: routineTitle }),
  });
}

export async function requestContact(routineId?: string): Promise<void> {
  await fetchAssistedAPI(`/api/users/${ASSISTED_USER_ID}/contact`, {
    method: 'POST',
    body: JSON.stringify({ routine_id: routineId ?? null }),
  });
}

