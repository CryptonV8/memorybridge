import { getIronSession } from 'iron-session';
import { cookies } from 'next/headers';

export interface SessionData {
  isDemoAuthenticated: boolean;
}

export const sessionOptions = {
  password: process.env.DEMO_SESSION_SECRET as string,
  cookieName: 'memorybridge_demo_session',
  cookieOptions: {
    secure: process.env.NODE_ENV === 'production',
    httpOnly: true,
    sameSite: 'lax' as const,
  },
};

export async function getSession() {
  const cookieStore = await cookies();
  const session = await getIronSession<SessionData>(cookieStore, sessionOptions);
  return session;
}
