'use server';

import { markRoutineDone, requestHelp, requestContact } from '@/lib/api-client';
import { revalidatePath } from 'next/cache';

export async function markDoneAction(routineId: string): Promise<{ error?: string }> {
  try {
    await markRoutineDone(routineId);
    revalidatePath('/today');
    return {};
  } catch (err) {
    return { error: err instanceof Error ? err.message : 'Could not mark routine as done.' };
  }
}

export async function helpAction(
  routineId: string,
  routineTitle: string
): Promise<{ error?: string }> {
  try {
    await requestHelp(routineId, routineTitle);
    revalidatePath('/today');
    return {};
  } catch (err) {
    return { error: err instanceof Error ? err.message : 'Could not send the help request.' };
  }
}

export async function contactAction(routineId?: string): Promise<{ error?: string }> {
  try {
    await requestContact(routineId);
    return {};
  } catch (err) {
    return { error: err instanceof Error ? err.message : 'Could not send the contact request.' };
  }
}
