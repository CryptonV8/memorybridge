'use server';

import { approveRoutine, rejectRoutine, updateRoutine } from '@/lib/api-client';
import { getSession } from '@/lib/session';
import { revalidatePath } from 'next/cache';

export async function approveDraft(routineId: string) {
  const session = await getSession();
  if (!session.isDemoAuthenticated) {
    return { error: 'Unauthorized demo session. Please login.' };
  }

  try {
    await approveRoutine(routineId);
    revalidatePath(`/caregiver/routines/${routineId}`);
    revalidatePath('/caregiver');
    return { success: true };
  } catch (error: any) {
    return { error: error.message || 'Failed to approve routine.' };
  }
}

export async function rejectDraft(routineId: string) {
  const session = await getSession();
  if (!session.isDemoAuthenticated) {
    return { error: 'Unauthorized demo session. Please login.' };
  }

  try {
    await rejectRoutine(routineId);
    revalidatePath(`/caregiver/routines/${routineId}`);
    revalidatePath('/caregiver');
    return { success: true };
  } catch (error: any) {
    return { error: error.message || 'Failed to reject routine.' };
  }
}

export async function editDraft(routineId: string, formData: FormData) {
  const session = await getSession();
  if (!session.isDemoAuthenticated) {
    return { error: 'Unauthorized demo session. Please login.' };
  }

  try {
    const title = formData.get('title') as string;
    const scheduled_time = formData.get('scheduled_time') as string;
    const purpose = formData.get('purpose') as string || '';
    const stepsRaw = formData.get('steps') as string;
    
    if (!title || title.trim().length === 0) {
      return { error: 'Title cannot be empty.' };
    }

    if (!scheduled_time) {
      return { error: 'Scheduled time is required.' };
    }

    let steps_json: string[] | undefined;
    if (stepsRaw) {
      steps_json = JSON.parse(stepsRaw) as string[];
      if (!Array.isArray(steps_json) || steps_json.length < 1 || steps_json.length > 5) {
        return { error: 'Routine must have between 1 and 5 steps.' };
      }
      for (const step of steps_json) {
        if (!step || step.trim().length === 0) {
          return { error: 'Steps cannot be empty.' };
        }
      }
    }

    await updateRoutine(routineId, {
      title,
      scheduled_time,
      purpose,
      steps_json
    });
    
    revalidatePath(`/caregiver/routines/${routineId}`);
    revalidatePath('/caregiver');
    return { success: true };
  } catch (error: any) {
    return { error: error.message || 'Failed to update routine.' };
  }
}

