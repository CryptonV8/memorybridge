'use server';

import { interpretRoutine } from '@/lib/api-client';
import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

export async function submitRoutine(formData: FormData) {
  const session = await getSession();
  if (!session.isDemoAuthenticated) {
    return { error: 'Unauthorized demo session. Please login.' };
  }

  const text = formData.get('instruction') as string;
  console.log(`[submitRoutine] Instruction text: "${text}"`);
  
  if (!text || text.trim().length === 0) {
    console.log('[submitRoutine] Error: Empty instruction');
    return { error: 'Instruction cannot be empty.' };
  }

  if (text.length > 500) {
    console.log('[submitRoutine] Error: Instruction too long');
    return { error: 'Instruction must be less than 500 characters.' };
  }

  try {
    console.log('[submitRoutine] Calling interpretRoutine...');
    const draft = await interpretRoutine(text);
    console.log(`[submitRoutine] interpretRoutine success. Draft ID: ${draft?.draft_id}`);
    
    if (draft && draft.draft_id) {
      console.log(`[submitRoutine] Redirecting to /caregiver/routines/${draft.draft_id}`);
      redirect(`/caregiver/routines/${draft.draft_id}`);
    } else {
       console.log('[submitRoutine] Error: draft or draft_id missing');
       return { error: 'Failed to create a draft. Please try again.' };
    }
  } catch (error: any) {
    console.log('[submitRoutine] Caught exception:', error);
    if (error && (error.digest?.startsWith('NEXT_REDIRECT') || error.message === 'NEXT_REDIRECT')) {
      console.log('[submitRoutine] Rethrowing NEXT_REDIRECT error:', error.digest || error.message);
      throw error;
    }
    console.log('[submitRoutine] Returning error object to client');
    // Return structured error safely without leaking raw stack trace to browser
    return { error: error.message || 'An unexpected error occurred while processing the routine.' };
  }
}
