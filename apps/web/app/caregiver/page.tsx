export const dynamic = 'force-dynamic';

import { listRoutines, getAlerts } from '@/lib/api-client';
import Link from 'next/link';
import { Routine, Alert } from '@/lib/api-schemas';
import { PlusCircle, AlertCircle, Clock, CheckCircle2, XCircle, HelpCircle } from 'lucide-react';
import { format, parseISO } from 'date-fns';

function getStatusIcon(status: Routine['status']) {
  switch (status) {
    case 'active':
      return <Clock className="h-5 w-5 text-blue-500" aria-label="Active" />;
    case 'completed':
      return <CheckCircle2 className="h-5 w-5 text-green-500" aria-label="Completed" />;
    case 'missed':
      return <XCircle className="h-5 w-5 text-red-500" aria-label="Missed" />;
    case 'help_requested':
      return <HelpCircle className="h-5 w-5 text-amber-500" aria-label="Help Requested" />;
    case 'rejected':
      return <XCircle className="h-5 w-5 text-slate-400" aria-label="Rejected" />;
    case 'draft':
    default:
      return <Clock className="h-5 w-5 text-slate-400" aria-label="Draft" />;
  }
}

function getStatusBadge(status: Routine['status'], approval_status: Routine['approval_status']) {
  if (approval_status === 'pending') {
    return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">Pending Review</span>;
  }

  switch (status) {
    case 'active':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">Active</span>;
    case 'completed':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Completed</span>;
    case 'missed':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Missed</span>;
    case 'help_requested':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">Help Requested</span>;
    case 'rejected':
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">Rejected</span>;
    default:
      return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">Draft</span>;
  }
}

export default async function CaregiverDashboard() {
  let routinesData;
  let alertsData: Alert[] = [];
  let isApiAvailable = true;
  let apiError = '';

  try {
    const [routinesResult, alertsResult] = await Promise.all([
      listRoutines(),
      getAlerts()
    ]);
    routinesData = routinesResult;
    alertsData = alertsResult;
  } catch (e: any) {
    isApiAvailable = false;
    apiError = e.message || 'Unable to connect to the backend API.';
  }

  const routines = routinesData?.routines || [];

  // Grouping
  const pendingReview = routines.filter(r => r.approval_status === 'pending');
  const active = routines.filter(r => r.status === 'active');
  const completed = routines.filter(r => r.status === 'completed');
  const needsAttention = routines.filter(r => r.status === 'help_requested' || r.status === 'missed');

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600 mt-1">Overview of Maria's routines and active alerts.</p>
        </div>
        <Link
          href="/caregiver/routines/new"
          className="inline-flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 transition-colors"
        >
          <PlusCircle className="-ml-1 mr-2 h-5 w-5" aria-hidden="true" />
          Create Routine
        </Link>
      </div>

      {!isApiAvailable && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-r-md">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">API Unavailable</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{apiError}. Please ensure the backend services are running.</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {alertsData.length > 0 && (
        <section aria-labelledby="alerts-heading">
          <h2 id="alerts-heading" className="text-lg font-medium text-slate-900 mb-4">Recent Alerts</h2>
          <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
            <ul className="divide-y divide-slate-200">
              {alertsData.slice(0, 3).map((alert) => (
                <li key={alert.id} className="p-4 hover:bg-slate-50 transition-colors">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-0.5">
                      <AlertCircle className={`h-5 w-5 ${alert.priority === 'high' ? 'text-red-500' : 'text-amber-500'}`} aria-hidden="true" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-slate-900">{alert.message}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        {alert.created_at ? format(parseISO(alert.created_at), 'MMM d, h:mm a') : 'Unknown time'}
                      </p>
                    </div>
                    <div>
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                        {alert.status}
                      </span>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
            {alertsData.length > 3 && (
              <div className="bg-slate-50 px-4 py-3 border-t border-slate-200 text-center sm:text-right">
                <Link href="/caregiver/alerts" className="text-sm font-medium text-blue-600 hover:text-blue-500">
                  View all alerts &rarr;
                </Link>
              </div>
            )}
          </div>
        </section>
      )}

      {isApiAvailable && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Pending Review */}
          <section aria-labelledby="pending-heading">
            <h2 id="pending-heading" className="text-lg font-medium text-slate-900 mb-4 flex items-center">
              Pending Review
              {pendingReview.length > 0 && (
                <span className="ml-2 bg-amber-100 text-amber-800 py-0.5 px-2 rounded-full text-xs font-medium">
                  {pendingReview.length}
                </span>
              )}
            </h2>
            {pendingReview.length > 0 ? (
              <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
                <ul className="divide-y divide-slate-200">
                  {pendingReview.map((routine) => (
                    <li key={routine.id}>
                      <Link href={`/caregiver/routines/${routine.id}`} className="block hover:bg-slate-50 focus:outline-none focus:bg-slate-50 transition-colors p-4">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium text-blue-600 truncate">{routine.title}</p>
                          <div className="ml-2 flex-shrink-0 flex">
                            {getStatusBadge(routine.status, routine.approval_status)}
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="flex items-center text-sm text-slate-500">
                              <Clock className="flex-shrink-0 mr-1.5 h-4 w-4 text-slate-400" aria-hidden="true" />
                              {routine.scheduled_time} {routine.timezone}
                            </p>
                          </div>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="bg-white shadow-sm rounded-lg border border-slate-200 p-6 text-center">
                <CheckCircle2 className="mx-auto h-8 w-8 text-slate-400" aria-hidden="true" />
                <p className="mt-2 text-sm text-slate-500">All caught up! No routines pending review.</p>
              </div>
            )}
          </section>

          {/* Active Routines */}
          <section aria-labelledby="active-heading">
            <h2 id="active-heading" className="text-lg font-medium text-slate-900 mb-4 flex items-center">
              Active Routines
            </h2>
            {active.length > 0 ? (
              <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
                <ul className="divide-y divide-slate-200">
                  {active.map((routine) => (
                    <li key={routine.id}>
                      <Link href={`/caregiver/routines/${routine.id}`} className="block hover:bg-slate-50 focus:outline-none focus:bg-slate-50 transition-colors p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            {getStatusIcon(routine.status)}
                            <p className="ml-2 text-sm font-medium text-slate-900 truncate">{routine.title}</p>
                          </div>
                          <div className="ml-2 flex-shrink-0 flex">
                            {getStatusBadge(routine.status, routine.approval_status)}
                          </div>
                        </div>
                        <div className="mt-2 sm:flex sm:justify-between">
                          <div className="sm:flex">
                            <p className="text-sm text-slate-500">
                              {routine.scheduled_time} {routine.timezone}
                            </p>
                          </div>
                        </div>
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <div className="bg-white shadow-sm rounded-lg border border-slate-200 p-6 text-center">
                <p className="text-sm text-slate-500">No active routines.</p>
              </div>
            )}
          </section>
        </div>
      )}

      {/* Needs Attention / Completed (Simple list at bottom) */}
      {isApiAvailable && (needsAttention.length > 0 || completed.length > 0) && (
        <section aria-labelledby="other-heading" className="mt-8">
          <h2 id="other-heading" className="text-lg font-medium text-slate-900 mb-4">Other Routines</h2>
          <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-slate-200">
            <ul className="divide-y divide-slate-200">
              {[...needsAttention, ...completed].map((routine) => (
                <li key={routine.id}>
                  <Link href={`/caregiver/routines/${routine.id}`} className="block hover:bg-slate-50 focus:outline-none focus:bg-slate-50 transition-colors p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center">
                        {getStatusIcon(routine.status)}
                        <p className="ml-2 text-sm font-medium text-slate-900 truncate">{routine.title}</p>
                      </div>
                      <div className="ml-2 flex-shrink-0 flex">
                        {getStatusBadge(routine.status, routine.approval_status)}
                      </div>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </div>
  );
}
