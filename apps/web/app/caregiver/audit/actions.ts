'use server';

import { getAuditEvents } from '@/lib/api-client';
import { getSession } from '@/lib/session';

export async function lookupAudit(formData: FormData) {
  const session = await getSession();
  if (!session.isDemoAuthenticated) {
    return { error: 'Unauthorized demo session. Please login.' };
  }

  const correlationId = formData.get('correlationId') as string;
  if (!correlationId) {
    return { error: 'Please provide a Correlation ID.' };
  }

  try {
    const events = await getAuditEvents(correlationId);
    return { events };
  } catch (error: any) {
    return { error: error.message || 'Failed to retrieve audit events.' };
  }
}
