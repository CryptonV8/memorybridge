export const dynamic = 'force-dynamic';

import { getAlerts } from '@/lib/api-client';
import { Alert } from '@/lib/api-schemas';
import { Bell, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import Link from 'next/link';

export default async function AlertsPage() {
  let alerts: Alert[] = [];
  let error = '';

  try {
    alerts = await getAlerts();
  } catch (err: any) {
    error = err.message || 'Failed to load alerts.';
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center space-x-4 mb-6">
        <Link href="/caregiver" className="text-slate-500 hover:text-slate-900 transition-colors min-h-[44px] flex items-center" aria-label="Back to Dashboard">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center">
            <Bell className="mr-2 h-6 w-6 text-slate-700" /> Caregiver Alerts
          </h1>
          <p className="text-slate-600 mt-1">Monitor notifications regarding Maria's routines and status.</p>
        </div>
      </div>

      {error ? (
        <div className="bg-red-50 p-4 rounded-md border border-red-200 flex items-start text-red-800" role="alert">
          <AlertCircle className="h-5 w-5 mr-3 flex-shrink-0" />
          <p>{error}</p>
        </div>
      ) : alerts.length === 0 ? (
        <div className="bg-white shadow-sm border border-slate-200 rounded-lg p-12 text-center">
          <CheckCircle2 className="mx-auto h-12 w-12 text-green-500 mb-4" />
          <h2 className="text-lg font-medium text-slate-900 mb-1">All Systems Normal</h2>
          <p className="text-slate-500">No active caregiver alerts at this time.</p>
        </div>
      ) : (
        <div className="bg-white shadow-sm border border-slate-200 rounded-lg overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-6 py-4 flex justify-between items-center">
            <h2 className="text-lg font-medium text-slate-900">Alert History</h2>
            <span className="bg-amber-100 text-amber-800 text-xs font-semibold px-2.5 py-0.5 rounded-full">
              {alerts.length} Total
            </span>
          </div>
          <ul className="divide-y divide-slate-200">
            {alerts.map((alert) => (
              <li key={alert.id} className="p-6 hover:bg-slate-50 transition-colors">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0 mt-1">
                    <AlertCircle className={`h-6 w-6 ${alert.priority === 'high' ? 'text-red-500' : 'text-amber-500'}`} aria-hidden="true" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium uppercase ${
                        alert.priority === 'high' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {alert.priority || 'normal'}
                      </span>
                      <span className="text-xs text-slate-500">
                        {alert.created_at ? format(parseISO(alert.created_at), 'MMM d, yyyy h:mm a') : 'Unknown time'}
                      </span>
                    </div>
                    <p className="text-slate-800 text-sm font-medium">{alert.message}</p>
                  </div>
                  <div className="flex-shrink-0">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 uppercase">
                      {alert.status}
                    </span>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

