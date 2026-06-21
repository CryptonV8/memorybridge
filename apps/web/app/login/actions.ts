'use server';

import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

export async function loginDemo(formData: FormData) {
  // In a real app we would check credentials. Here we just set the demo session.
  const session = await getSession();
  session.isDemoAuthenticated = true;
  await session.save();
  redirect('/caregiver');
}

export async function logoutDemo() {
  const session = await getSession();
  session.destroy();
  redirect('/login');
}
