'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { lookupAudit } from './actions';
import { AuditEvent } from '@/lib/api-schemas';
import { Search, Shield, AlertTriangle, FileText, ArrowLeft, Loader2 } from 'lucide-react';
import Link from 'next/link';

function AuditPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const defaultCorrelationId = searchParams.get('correlationId') || '';
  
  const [correlationId, setCorrelationId] = useState(defaultCorrelationId);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  useEffect(() => {
    if (defaultCorrelationId) {
      handleLookup(defaultCorrelationId);
    }
  }, [defaultCorrelationId]);

  async function handleLookup(idToLookup: string) {
    if (!idToLookup.trim()) return;
    setLoading(true);
    setError('');
    setSearched(true);
    
    const formData = new FormData();
    formData.append('correlationId', idToLookup.trim());
    
    const result = await lookupAudit(formData);
    
    if (result.error) {
      setError(result.error);
      setEvents([]);
    } else if (result.events) {
      setEvents(result.events);
      if (result.events.length === 0) {
        setError('No audit events found for this correlation ID.');
      }
    }
    setLoading(false);
  }

  function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    router.push(`/caregiver/audit?correlationId=${encodeURIComponent(correlationId)}`);
    handleLookup(correlationId);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center space-x-4 mb-6">
        <Link href="/caregiver" className="text-slate-500 hover:text-slate-900 transition-colors">
          <ArrowLeft className="h-5 w-5" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center">
            <Shield className="mr-2 h-6 w-6 text-slate-700" /> System Audit Log
          </h1>
          <p className="text-slate-600 mt-1">Review redacted system decisions and tool executions.</p>
        </div>
      </div>

      <div className="bg-white shadow-sm border border-slate-200 rounded-lg p-6">
        <form onSubmit={onSubmit} className="flex gap-4">
          <div className="flex-1">
            <label htmlFor="correlationId" className="sr-only">Correlation ID</label>
            <div className="relative rounded-md shadow-sm">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <Search className="h-5 w-5 text-slate-400" aria-hidden="true" />
              </div>
              <input
                type="text"
                name="correlationId"
                id="correlationId"
                className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 sm:text-sm border-slate-300 rounded-md border p-2.5"
                placeholder="Enter Correlation ID (e.g. uuid)"
                value={correlationId}
                onChange={(e) => setCorrelationId(e.target.value)}
                required
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={loading || !correlationId.trim()}
            className="inline-flex justify-center items-center py-2.5 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 className="animate-spin h-5 w-5" /> : 'Lookup Logs'}
          </button>
        </form>
      </div>

      {error && (
        <div className="bg-amber-50 p-4 rounded-md border border-amber-200 flex items-start text-amber-800">
          <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
          <p>{error}</p>
        </div>
      )}

      {events.length > 0 && (
        <div className="bg-white shadow-sm border border-slate-200 rounded-lg overflow-hidden">
          <div className="border-b border-slate-200 bg-slate-50 px-6 py-4">
            <h3 className="text-lg font-medium text-slate-900">Audit Trail: {correlationId}</h3>
          </div>
          <ul className="divide-y divide-slate-200">
            {events.map((event, index) => (
              <li key={event.id} className="p-6 hover:bg-slate-50 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className="h-8 w-8 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-medium text-sm border border-slate-200">
                      {index + 1}
                    </span>
                    <span className="font-semibold text-slate-900">{event.tool_name}</span>
                  </div>
                  <span className="text-sm text-slate-500">
                    {new Date(event.created_at).toLocaleString()}
                  </span>
                </div>
                
                <div className="ml-11 mt-2">
                  <div className="flex space-x-4 text-sm mb-3">
                    <span className="text-slate-600 font-medium">Event: <span className="text-slate-900 font-normal">{event.event_type}</span></span>
                    <span className="text-slate-600 font-medium">Decision: 
                      <span className={`ml-1 px-2 py-0.5 rounded text-xs font-medium ${
                        event.decision === 'rejected' || event.decision === 'reject_prohibited' ? 'bg-red-100 text-red-800' :
                        event.decision === 'approved' || event.decision === 'allow_for_review' || event.decision === 'allowed' ? 'bg-green-100 text-green-800' :
                        'bg-slate-100 text-slate-800'
                      }`}>
                        {event.decision}
                      </span>
                    </span>
                  </div>
                  
                  {Object.keys(event.metadata).length > 0 && (
                    <div className="bg-slate-50 border border-slate-200 rounded-md p-3 text-sm font-mono text-slate-700 overflow-x-auto">
                      <div className="flex items-center text-xs text-slate-500 mb-2 uppercase tracking-wider font-sans">
                        <FileText className="h-3 w-3 mr-1" /> Redacted Metadata
                      </div>
                      <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                    </div>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function AuditPage() {
  return (
    <Suspense fallback={<div className="flex justify-center p-8"><Loader2 className="animate-spin text-slate-500" /></div>}>
      <AuditPageContent />
    </Suspense>
  );
}
