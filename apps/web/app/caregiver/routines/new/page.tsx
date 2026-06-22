'use client';

import { useState } from 'react';
import { submitRoutine } from './actions';
import { AlertCircle, ArrowLeft, Loader2, Info } from 'lucide-react';
import Link from 'next/link';

export default function NewRoutinePage() {
  const [instruction, setInstruction] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');

  const characterLimit = 500;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    const formData = new FormData(e.currentTarget);
    const result = await submitRoutine(formData);

    // If it returns, there was an error (success redirects)
    if (result && result.error) {
      setError(result.error);
      setIsSubmitting(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center space-x-4 mb-6">
        <Link href="/caregiver" className="text-slate-500 hover:text-slate-900 transition-colors" aria-label="Back to dashboard">
          <ArrowLeft className="h-5 w-5" aria-hidden="true" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Create Routine</h1>
          <p className="text-slate-600 mt-1">Describe a new routine for Maria in natural language.</p>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-r-md" role="alert" aria-live="assertive">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow-sm rounded-lg border border-slate-200 overflow-hidden">
        <div className="p-6 space-y-6">
          <div>
            <label htmlFor="instruction" className="block text-sm font-medium text-slate-900 mb-2">
              Routine Instructions
            </label>
            <div className="mt-1">
              <textarea
                id="instruction"
                name="instruction"
                rows={4}
                className="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-slate-300 rounded-md p-3 border"
                placeholder="e.g., Please remind Maria at 10:00 to water the plants near the living-room window."
                value={instruction}
                onChange={(e) => setInstruction(e.target.value)}
                maxLength={characterLimit}
                disabled={isSubmitting}
                aria-describedby="instruction-description"
                required
              />
            </div>
            <div className="mt-2 flex justify-between items-center text-sm">
              <p id="instruction-description" className="text-slate-500">
                Be specific about the task and the time. Keep it simple.
              </p>
              <span className={`font-medium ${instruction.length > characterLimit - 50 ? 'text-amber-500' : 'text-slate-400'}`}>
                {instruction.length} / {characterLimit}
              </span>
            </div>
          </div>

          <div className="bg-slate-50 rounded-lg p-4 border border-slate-100 flex items-start space-x-3">
            <Info className="h-5 w-5 text-slate-400 mt-0.5 flex-shrink-0" aria-hidden="true" />
            <div className="text-sm text-slate-600">
              <p className="font-medium text-slate-900 mb-1">MVP Limitations</p>
              <p>The system is designed for safe, low-risk daily tasks. It will reject routines involving:</p>
              <ul className="list-disc pl-4 mt-2 space-y-1">
                <li>Medication changes or doses</li>
                <li>Financial actions or transactions</li>
                <li>Stove, oven, or dangerous appliance use</li>
                <li>Medical decisions</li>
                <li>Emergency actions</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end">
          <Link
            href="/caregiver"
            className="bg-white py-2 px-4 border border-slate-300 rounded-md shadow-sm text-sm font-medium text-slate-700 hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 mr-3"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={isSubmitting || instruction.trim().length === 0}
            className="inline-flex justify-center items-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-slate-900 hover:bg-slate-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-slate-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" aria-hidden="true" />
                Processing Draft...
              </>
            ) : (
              'Generate Draft'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
