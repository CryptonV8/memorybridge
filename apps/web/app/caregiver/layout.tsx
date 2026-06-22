import Link from 'next/link';
import { logoutDemo } from '../login/actions';
import { AlertTriangle, Home, PlusCircle, Bell, Clock, LogOut } from 'lucide-react';

export default function CaregiverLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900">
      {/* Skip Navigation Link for Accessibility */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-white text-blue-600 px-4 py-2 rounded shadow-md z-50 font-medium"
      >
        Skip to main content
      </a>

      {/* Persistent Demo Banner */}
      <div className="bg-amber-100 text-amber-900 px-4 py-3 flex items-center justify-center space-x-2 border-b border-amber-200">
        <AlertTriangle className="h-5 w-5" aria-hidden="true" />
        <p className="font-medium text-sm sm:text-base text-center">
          Demo only. Synthetic data. MemoryBridge is not a medical device and does not replace caregivers or healthcare professionals.
        </p>
      </div>

      {/* Main Header / Nav */}
      <header className="bg-white border-b border-slate-200 shadow-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-xl text-slate-900 tracking-tight">MemoryBridge</span>
              <span className="bg-blue-100 text-blue-800 text-xs font-semibold px-2 py-0.5 rounded">Caregiver</span>
            </div>
            
            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-6" aria-label="Primary navigation">
              <Link href="/caregiver" className="flex items-center space-x-1.5 text-slate-600 hover:text-slate-900 font-medium transition-colors">
                <Home className="h-4 w-4" aria-hidden="true" />
                <span>Dashboard</span>
              </Link>
              <Link href="/caregiver/routines/new" className="flex items-center space-x-1.5 text-slate-600 hover:text-slate-900 font-medium transition-colors">
                <PlusCircle className="h-4 w-4" aria-hidden="true" />
                <span>Create Routine</span>
              </Link>
              <Link href="/caregiver/alerts" className="flex items-center space-x-1.5 text-slate-600 hover:text-slate-900 font-medium transition-colors">
                <Bell className="h-4 w-4" aria-hidden="true" />
                <span>Alerts</span>
              </Link>
              <Link href="/caregiver/audit" className="flex items-center space-x-1.5 text-slate-600 hover:text-slate-900 font-medium transition-colors">
                <Clock className="h-4 w-4" aria-hidden="true" />
                <span>Audit</span>
              </Link>
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-sm font-medium text-slate-900">Anna Petrova</span>
              <span className="text-xs text-slate-500">Supporting: Maria Petrova</span>
            </div>
            <form action={logoutDemo}>
              <button 
                type="submit"
                className="flex items-center space-x-1.5 text-slate-500 hover:text-red-600 font-medium transition-colors focus:ring-2 focus:ring-red-500 focus:outline-none rounded px-2 py-1"
                aria-label="Log out of demo"
              >
                <LogOut className="h-4 w-4" aria-hidden="true" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </form>
          </div>
        </div>

        {/* Mobile Navigation */}
        <nav className="md:hidden border-t border-slate-100 bg-white flex overflow-x-auto" aria-label="Mobile navigation">
          <Link href="/caregiver" className="flex-1 min-w-[80px] py-3 flex flex-col items-center space-y-1 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors">
            <Home className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] font-medium">Dashboard</span>
          </Link>
          <Link href="/caregiver/routines/new" className="flex-1 min-w-[80px] py-3 flex flex-col items-center space-y-1 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors">
            <PlusCircle className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] font-medium">Create</span>
          </Link>
          <Link href="/caregiver/alerts" className="flex-1 min-w-[80px] py-3 flex flex-col items-center space-y-1 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors">
            <Bell className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] font-medium">Alerts</span>
          </Link>
          <Link href="/caregiver/audit" className="flex-1 min-w-[80px] py-3 flex flex-col items-center space-y-1 text-slate-600 hover:text-slate-900 hover:bg-slate-50 transition-colors">
            <Clock className="h-5 w-5" aria-hidden="true" />
            <span className="text-[10px] font-medium">Audit</span>
          </Link>
        </nav>
      </header>

      {/* Main Content Area */}
      <main id="main-content" className="flex-grow max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 focus:outline-none" tabIndex={-1}>
        {children}
      </main>
    </div>
  );
}
