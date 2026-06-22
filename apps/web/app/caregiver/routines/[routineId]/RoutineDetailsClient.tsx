'use client';

import { useState } from 'react';
import { Routine } from '@/lib/api-schemas';
import { approveDraft, rejectDraft, editDraft } from './actions';
import { ArrowLeft, CheckCircle, XCircle, AlertTriangle, ShieldAlert, Clock, ListChecks, Edit2, ShieldCheck, FileText, Settings, Loader2, Plus, Trash2 } from 'lucide-react';
import Link from 'next/link';

interface RoutineDetailsClientProps {
  routine: Routine;
}

export function RoutineDetailsClient({ routine: initialRoutine }: RoutineDetailsClientProps) {
  const [routine, setRoutine] = useState<Routine>(initialRoutine);
  
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState(routine.title);
  const [editTime, setEditTime] = useState(routine.scheduled_time || '');
  const [editPurpose, setEditPurpose] = useState(routine.purpose || '');
  const [editSteps, setEditSteps] = useState<string[]>(routine.steps_json || []);
  
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  
  // Explicit approval checkbox
  const [isApprovedConfirmed, setIsApprovedConfirmed] = useState(false);

  const metadata = (routine.metadata || {}) as {
    policy_reasons?: string[];
    original_instruction?: string;
    missing_information?: string[];
    visible_steps?: string[];
    help_text?: string;
  };
  
  const isDraftOrPending = routine.status === 'draft' || routine.status === 'pending_approval';
  const isProhibited = routine.safety_decision === 'reject_prohibited';
  const isMediumRisk = routine.safety_decision === 'reject_medium_risk';
  const canApprove = isDraftOrPending && routine.safety_decision === 'allow_for_review';

  async function handleApprove() {
    if (!isApprovedConfirmed) {
      setError('You must confirm review of the routine before approving.');
      return;
    }
    
    setError('');
    setIsApproving(true);
    const result = await approveDraft(routine.id);
    if (result.error) {
      setError(result.error);
    } else {
      // Reload page to refresh RSC state
      window.location.reload();
    }
    setIsApproving(false);
  }

  async function handleReject() {
    if (confirm("Are you sure you want to reject this draft? It cannot be approved later.")) {
      setError('');
      setIsRejecting(true);
      const result = await rejectDraft(routine.id);
      if (result.error) {
        setError(result.error);
      } else {
        window.location.reload();
      }
      setIsRejecting(false);
    }
  }

  // Edit Steps Helpers
  function handleStepChange(index: number, value: string) {
    const newSteps = [...editSteps];
    newSteps[index] = value;
    setEditSteps(newSteps);
  }

  function handleAddStep() {
    if (editSteps.length < 5) {
      setEditSteps([...editSteps, '']);
    }
  }

  function handleRemoveStep(index: number) {
    if (editSteps.length > 1) {
      const newSteps = editSteps.filter((_, i) => i !== index);
      setEditSteps(newSteps);
    }
  }

  async function handleSaveEdit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');

    // Validation checks
    if (!editTitle.trim()) {
      setError('Title cannot be empty.');
      return;
    }
    if (!editTime) {
      setError('Scheduled time is required.');
      return;
    }
    if (editSteps.length < 1 || editSteps.length > 5) {
      setError('Routine must have between 1 and 5 steps.');
      return;
    }
    for (let i = 0; i < editSteps.length; i++) {
      if (!editSteps[i].trim()) {
        setError(`Step ${i + 1} cannot be empty.`);
        return;
      }
    }

    setIsSaving(true);
    const formData = new FormData();
    formData.append('title', editTitle.trim());
    formData.append('scheduled_time', editTime);
    formData.append('purpose', editPurpose.trim());
    formData.append('steps', JSON.stringify(editSteps.map(s => s.trim())));
    
    const result = await editDraft(routine.id, formData);
    if (result.error) {
      setError(result.error);
    } else {
      setIsEditing(false);
      window.location.reload();
    }
    setIsSaving(false);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <Link href="/caregiver" className="flex items-center text-slate-500 hover:text-slate-900 font-medium transition-colors min-h-[44px]">
          <ArrowLeft className="mr-2 h-5 w-5" /> Back to Dashboard
        </Link>
        {routine.correlation_id && (
          <Link href={`/caregiver/audit?correlationId=${routine.correlation_id}`} className="text-sm font-medium text-blue-600 hover:text-blue-500 transition-colors min-h-[44px] flex items-center">
            View Audit Timeline
          </Link>
        )}
      </div>

      {error && (
        <div className="bg-red-50 border-l-4 border-red-400 p-4 rounded-r-md" role="alert" aria-live="assertive">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertTriangle className="h-5 w-5 text-red-400" aria-hidden="true" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white shadow-sm border border-slate-200 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="border-b border-slate-200 px-6 py-5 bg-slate-50 flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{routine.title}</h1>
            <div className="mt-1 flex items-center space-x-4 text-sm text-slate-500">
              <span className="flex items-center">
                <Clock className="mr-1.5 h-4 w-4" /> {routine.scheduled_time} {routine.timezone}
              </span>
              <span className="flex items-center capitalize">
                <Settings className="mr-1.5 h-4 w-4" /> Status: {routine.status.replace('_', ' ')}
              </span>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              routine.risk_level === 'low' ? 'bg-green-100 text-green-800' :
              routine.risk_level === 'medium' ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800'
            }`}>
              {routine.risk_level.toUpperCase()} RISK
            </span>
          </div>
        </div>

        {/* Content */}
        <div className="px-6 py-6 space-y-8">
          
          {/* Policy and Safety Warning */}
          {(isProhibited || isMediumRisk) && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-r-md">
              <div className="flex">
                <ShieldAlert className="h-6 w-6 text-red-500 mr-3 flex-shrink-0" />
                <div>
                  <h2 className="text-red-800 font-medium text-lg">Routine Blocked by Safety Policy</h2>
                  <div className="mt-2 text-sm text-red-700 space-y-1">
                    <p>MemoryBridge does not automate this type of routine in the current safety profile.</p>
                    {metadata.policy_reasons && metadata.policy_reasons.length > 0 && (
                      <ul className="list-disc pl-5 mt-2 space-y-1">
                        {metadata.policy_reasons.map((reason: string, i: number) => (
                          <li key={i}>{reason}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Original Instruction */}
          {metadata.original_instruction && (
            <div>
              <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center">
                <FileText className="h-4 w-4 mr-2" /> Original Instruction
              </h2>
              <p className="text-slate-800 italic bg-slate-50 p-4 rounded-md border border-slate-100 text-sm">
                "{metadata.original_instruction}"
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Draft Details / Edit Form */}
            <div>
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider flex items-center">
                  <ListChecks className="h-4 w-4 mr-2" /> AI Structured Draft
                </h2>
                {isDraftOrPending && !isEditing && (
                  <button 
                    onClick={() => setIsEditing(true)} 
                    className="text-slate-500 hover:text-blue-600 transition-colors flex items-center text-sm font-medium min-h-[44px] px-2 rounded hover:bg-slate-100" 
                    aria-label="Edit draft details"
                  >
                    <Edit2 className="h-4 w-4 mr-1.5" /> Edit Draft
                  </button>
                )}
              </div>
              
              {isEditing ? (
                <form onSubmit={handleSaveEdit} className="space-y-4 bg-slate-50 p-4 rounded-md border border-slate-200" aria-label="Edit routine draft form">
                  <div>
                    <label htmlFor="edit-title" className="block text-sm font-medium text-slate-700">Title</label>
                    <input 
                      id="edit-title"
                      type="text" 
                      value={editTitle} 
                      onChange={e => setEditTitle(e.target.value)} 
                      required 
                      className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2 bg-white" 
                    />
                  </div>
                  
                  <div>
                    <label htmlFor="edit-time" className="block text-sm font-medium text-slate-700">Scheduled Time</label>
                    <input 
                      id="edit-time"
                      type="time" 
                      value={editTime} 
                      onChange={e => setEditTime(e.target.value)} 
                      required 
                      className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2 bg-white" 
                    />
                  </div>

                  <div>
                    <label htmlFor="edit-purpose" className="block text-sm font-medium text-slate-700">Purpose / Notes</label>
                    <textarea 
                      id="edit-purpose"
                      value={editPurpose} 
                      onChange={e => setEditPurpose(e.target.value)} 
                      rows={2}
                      className="mt-1 block w-full rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2 bg-white" 
                    />
                  </div>

                  <div className="space-y-2">
                    <span className="block text-sm font-medium text-slate-700">Steps ({editSteps.length} of 5)</span>
                    <p className="text-xs text-slate-500 italic">Each step should describe exactly one clear action.</p>
                    
                    <div className="space-y-3">
                      {editSteps.map((step, idx) => (
                        <div key={idx} className="flex items-center space-x-2">
                          <label htmlFor={`edit-step-${idx}`} className="sr-only">Step {idx + 1}</label>
                          <span className="flex-shrink-0 h-8 w-8 rounded-full bg-slate-200 flex items-center justify-center text-xs font-semibold text-slate-700">{idx + 1}</span>
                          <input 
                            id={`edit-step-${idx}`}
                            type="text" 
                            value={step} 
                            onChange={e => handleStepChange(idx, e.target.value)} 
                            required 
                            placeholder={`Action for step ${idx + 1}`}
                            className="block flex-grow rounded-md border-slate-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm border p-2 bg-white" 
                          />
                          {editSteps.length > 1 && (
                            <button
                              type="button"
                              onClick={() => handleRemoveStep(idx)}
                              className="text-red-500 hover:text-red-700 p-2 min-h-[44px] min-w-[44px] flex items-center justify-center rounded hover:bg-red-50 transition-colors"
                              aria-label={`Remove step ${idx + 1}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      ))}
                    </div>

                    {editSteps.length < 5 && (
                      <button
                        type="button"
                        onClick={handleAddStep}
                        className="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium flex items-center min-h-[44px] px-3 rounded hover:bg-blue-50 transition-colors"
                      >
                        <Plus className="h-4 w-4 mr-1" /> Add Step
                      </button>
                    )}
                  </div>

                  <div className="flex space-x-2 pt-2 border-t border-slate-200">
                    <button 
                      type="submit" 
                      disabled={isSaving} 
                      className="bg-slate-900 text-white px-4 py-2 rounded text-sm font-medium hover:bg-slate-800 disabled:opacity-50 flex items-center min-h-[44px] cursor-pointer"
                    >
                      {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Save Edits
                    </button>
                    <button 
                      type="button" 
                      onClick={() => {
                        setIsEditing(false);
                        setError('');
                        setEditTitle(routine.title);
                        setEditTime(routine.scheduled_time || '');
                        setEditPurpose(routine.purpose || '');
                        setEditSteps(routine.steps_json || []);
                      }} 
                      className="bg-white border border-slate-300 text-slate-700 px-4 py-2 rounded text-sm font-medium hover:bg-slate-50 min-h-[44px] cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <div className="bg-white border border-slate-200 rounded-md p-4 relative">
                  <h3 className="font-semibold text-slate-900 mb-1">{routine.title}</h3>
                  <p className="text-sm text-slate-500 mb-2">{routine.scheduled_time} {routine.timezone}</p>
                  {routine.purpose && (
                    <p className="text-sm text-slate-600 mb-4 bg-slate-50 p-2.5 rounded border border-slate-100 font-sans italic">{routine.purpose}</p>
                  )}
                  <ul className="space-y-2">
                    {routine.steps_json.map((step, idx) => (
                      <li key={idx} className="flex items-start text-sm text-slate-700">
                        <span className="flex-shrink-0 h-5 w-5 rounded-full bg-slate-100 flex items-center justify-center text-xs font-semibold text-slate-500 mr-3 mt-0.5 border border-slate-200">{idx + 1}</span>
                        <span className="mt-0.5">{step}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {metadata.missing_information && metadata.missing_information.length > 0 && (
                <div className="mt-4 bg-amber-50 border border-amber-200 p-4 rounded-md">
                  <h3 className="text-sm font-semibold text-amber-800 flex items-center">
                    <AlertTriangle className="h-4 w-4 mr-2" /> Missing Information Identified
                  </h3>
                  <ul className="mt-2 text-sm text-amber-700 list-disc pl-5 space-y-1">
                    {metadata.missing_information.map((info: string, i: number) => (
                      <li key={i}>{info}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Generated Wording and Safety */}
            <div className="space-y-6">
              <div>
                <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center">
                  <ShieldCheck className="h-4 w-4 mr-2" /> Semantic Safety Review
                </h2>
                <div className="bg-slate-50 p-4 rounded-md border border-slate-200 text-sm text-slate-700">
                  <p className="font-semibold mb-2 flex items-center">
                    {routine.safety_decision === 'allow_for_review' ? (
                      <><CheckCircle className="h-4 w-4 text-green-500 mr-2" /> Passed semantic review</>
                    ) : (
                      <><XCircle className="h-4 w-4 text-red-500 mr-2" /> Failed semantic review</>
                    )}
                  </p>
                  {metadata.policy_reasons && metadata.policy_reasons.length > 0 && (
                    <ul className="list-disc pl-5 space-y-1 mt-2 text-slate-600">
                      {metadata.policy_reasons.map((reason: string, i: number) => (
                        <li key={i}>{reason}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {metadata.visible_steps && metadata.visible_steps.length > 0 && (
                <div>
                  <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3 flex items-center">
                    <FileText className="h-4 w-4 mr-2" /> Dementia-Friendly Wording
                  </h2>
                  <div className="bg-blue-50 border border-blue-100 p-4 rounded-md text-sm text-slate-800">
                    <p className="text-xs text-slate-500 mb-2 font-medium uppercase tracking-wider">What Maria will see</p>
                    <ul className="space-y-2">
                      {metadata.visible_steps.map((step: string, i: number) => (
                        <li key={i} className="flex items-start">
                          <CheckCircle className="h-4 w-4 text-blue-500 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="font-medium text-blue-900">{step}</span>
                        </li>
                      ))}
                    </ul>
                    {metadata.help_text && (
                      <p className="mt-3 text-slate-600 italic">"{metadata.help_text}"</p>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Confirmation & Footer */}
        <div className="bg-slate-50 border-t border-slate-200 px-6 py-6 flex flex-col space-y-4">
          {/* Approval Confirmation Checkbox & Summary */}
          {canApprove && (
            <div className="bg-white border border-slate-200 rounded-md p-4 space-y-3">
              <h3 className="font-semibold text-slate-900 text-sm">Review Activation Summary</h3>
              <div className="text-xs text-slate-600 bg-slate-50 p-3 rounded border border-slate-100 space-y-1">
                <p><strong>Title:</strong> {routine.title}</p>
                <p><strong>Scheduled Time:</strong> {routine.scheduled_time} {routine.timezone}</p>
                <p><strong>Steps to show Maria:</strong></p>
                <ul className="list-decimal pl-4 space-y-0.5">
                  {(metadata.visible_steps && metadata.visible_steps.length > 0 ? metadata.visible_steps : routine.steps_json).map((s, i) => (
                    <li key={i}>{s}</li>
                  ))}
                </ul>
              </div>
              
              <div className="flex items-start">
                <div className="flex items-center h-5">
                  <input
                    id="confirm-approval"
                    name="confirm-approval"
                    type="checkbox"
                    checked={isApprovedConfirmed}
                    onChange={(e) => {
                      setIsApprovedConfirmed(e.target.checked);
                      setError('');
                    }}
                    className="focus:ring-green-500 h-5 w-5 text-green-600 border-slate-300 rounded cursor-pointer"
                  />
                </div>
                <div className="ml-3 text-sm">
                  <label htmlFor="confirm-approval" className="font-medium text-slate-700 cursor-pointer">
                    I confirm that I have reviewed the generated wording and active steps, and verify they are safe for Maria Petrova.
                  </label>
                </div>
              </div>
            </div>
          )}

          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              {isDraftOrPending && (
                 <p className="text-sm text-amber-800 font-medium flex items-center">
                   <AlertTriangle className="h-4 w-4 mr-1.5" /> AI-generated draft — caregiver review required
                 </p>
              )}
              {routine.status === 'active' && (
                <p className="text-sm text-green-700 font-medium flex items-center">
                  <CheckCircle className="h-4 w-4 mr-1.5" /> Routine is currently active
                </p>
              )}
              {routine.status === 'rejected' && (
                <p className="text-sm text-red-700 font-medium flex items-center">
                  <XCircle className="h-4 w-4 mr-1.5" /> Routine was rejected and cannot be activated
                </p>
              )}
            </div>
            
            <div className="flex space-x-3 w-full sm:w-auto">
              {isDraftOrPending && (
                <button
                  onClick={handleReject}
                  disabled={isRejecting || isApproving || isSaving}
                  className="flex-grow sm:flex-none justify-center items-center px-4 py-2 border border-slate-300 text-sm font-medium rounded-md text-slate-700 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 transition-colors min-h-[44px] cursor-pointer"
                >
                  {isRejecting ? 'Rejecting...' : 'Reject Draft'}
                </button>
              )}
              
              {canApprove && (
                <button
                  onClick={handleApprove}
                  disabled={isRejecting || isApproving || isSaving || !isApprovedConfirmed}
                  className="flex-grow sm:flex-none justify-center items-center px-6 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 transition-colors min-h-[44px] cursor-pointer"
                >
                  {isApproving ? 'Approving...' : 'Approve & Activate'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
