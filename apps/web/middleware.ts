import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';
import { getIronSession } from 'iron-session';
import { sessionOptions, SessionData } from './lib/session';

export async function middleware(request: NextRequest) {
  const response = NextResponse.next();
  const session = await getIronSession<SessionData>(request, response, sessionOptions);

  console.log(`Middleware path: ${request.nextUrl.pathname}, method: ${request.method}, auth: ${session.isDemoAuthenticated}`);

  if (!session.isDemoAuthenticated) {
    console.log(`Redirecting to /login due to unauthenticated session. Cookies:`, request.cookies.getAll());
    const loginUrl = new URL('/login', request.url);
    return NextResponse.redirect(loginUrl);
  }

  return response;
}

export const config = {
  matcher: ['/caregiver/:path*'],
};
