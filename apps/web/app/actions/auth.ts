'use server';

import { getSession } from '@/lib/session';
import { redirect } from 'next/navigation';

export async function login() {
  const session = await getSession();
  session.isDemoAuthenticated = true;
  await session.save();
  redirect('/caregiver');
}

export async function logout() {
  const session = await getSession();
  session.destroy();
  redirect('/login');
}
