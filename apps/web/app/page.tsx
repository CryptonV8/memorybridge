import { redirect } from 'next/navigation';
import { getSession } from '@/lib/session';

export default async function Home() {
  const session = await getSession();
  
  if (session.isDemoAuthenticated) {
    redirect('/caregiver');
  } else {
    redirect('/login');
  }
}
