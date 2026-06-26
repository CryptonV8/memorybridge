export const dynamic = 'force-dynamic';

import { getRoutine } from '@/lib/api-client';
import { RoutineDetailsClient } from './RoutineDetailsClient';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import Link from 'next/link';

export default async function RoutineDetailsPage({ params }: { params: Promise<{ routineId: string }> }) {
  try {
    const { routineId } = await params;
    const routine = await getRoutine(routineId);
    return <RoutineDetailsClient routine={routine} />;
  } catch (err: any) {
    const error = err.message || 'Failed to load routine.';
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <Link href="/caregiver" className="flex items-center text-slate-500 hover:text-slate-900 font-medium transition-colors min-h-[44px]">
          <ArrowLeft className="mr-2 h-5 w-5" /> Back to Dashboard
        </Link>
        <div className="bg-red-50 p-6 rounded-lg flex items-start space-x-4 border border-red-200" role="alert">
          <AlertTriangle className="h-6 w-6 text-red-500 flex-shrink-0" />
          <div>
            <h2 className="text-red-800 font-medium text-lg">Unable to load routine</h2>
            <p className="text-red-700 mt-1">{error}</p>
            <Link href="/caregiver" className="mt-4 inline-flex items-center text-sm font-medium text-red-800 hover:text-red-900 transition-colors min-h-[44px]">
              &larr; Return to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }
}

