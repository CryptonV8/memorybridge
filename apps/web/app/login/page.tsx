import { loginDemo } from './actions';

export default function LoginPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 text-slate-900 p-4">
      <div className="max-w-md w-full bg-white p-8 rounded-xl shadow-sm border border-slate-200">
        <h1 className="text-2xl font-semibold mb-2">MemoryBridge Demo</h1>
        <p className="text-slate-600 mb-6">
          This is a demonstration environment. No real data or actual production authentication is used.
        </p>
        
        <form action={loginDemo}>
          <button
            type="submit"
            className="w-full bg-slate-900 text-white font-medium py-3 px-4 rounded-lg hover:bg-slate-800 transition-colors focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 outline-none"
          >
            Enter Demo Environment
          </button>
        </form>

        <div className="mt-6 text-sm text-slate-500 bg-slate-50 p-4 rounded-lg">
          <p className="font-medium text-slate-700 mb-1">Notice:</p>
          <ul className="list-disc pl-4 space-y-1">
            <li>No Caregiver tokens are stored in the browser.</li>
            <li>Authentication is a simple server-side gate.</li>
            <li>Routine data is generated deterministically for testing.</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
