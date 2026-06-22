import { z } from 'zod';

export const RoutineSchema = z.object({
  id: z.string().uuid(),
  assisted_user_id: z.string().uuid(),
  title: z.string(),
  purpose: z.string().nullable(),
  scheduled_time: z.string(),
  timezone: z.string(),
  steps_json: z.array(z.string()),
  risk_level: z.enum(['low', 'medium', 'prohibited']),
  safety_decision: z.enum(['allow_for_review', 'reject_medium_risk', 'reject_prohibited']),
  approval_status: z.enum(['pending', 'approved', 'rejected']),
  status: z.enum(['draft', 'pending_approval', 'active', 'completed', 'help_requested', 'missed', 'rejected']),
  correlation_id: z.string().uuid().nullable().optional(),
  metadata: z.record(z.string(), z.any()).nullable().optional(),
});

export type Routine = z.infer<typeof RoutineSchema>;

export const AuditEventSchema = z.object({
  id: z.string().uuid(),
  correlation_id: z.string().uuid(),
  tool_name: z.string(),
  event_type: z.string(),
  decision: z.string(),
  metadata: z.record(z.string(), z.any()),
  created_at: z.string(),
});

export type AuditEvent = z.infer<typeof AuditEventSchema>;

export const AlertSchema = z.object({
  id: z.string().uuid(),
  caregiver_user_id: z.string().uuid(),
  message: z.string(),
  status: z.enum(['unread', 'read']),
  priority: z.enum(['low', 'normal', 'high']).optional(),
  created_at: z.string().optional(),
});

export type Alert = z.infer<typeof AlertSchema>;

export const PaginatedRoutinesSchema = z.object({
  items: z.array(RoutineSchema),
  next_cursor: z.string().nullable(),
});

export const InterpretationDraftSchema = z.object({
  draft_id: z.string().uuid(),
  title: z.string(),
  scheduled_time: z.string(),
  steps: z.array(z.string()),
  safety_decision: z.string(),
  policy_reasons: z.array(z.string()),
  visible_steps: z.array(z.string()).nullable().optional(),
  help_text: z.string().nullable().optional(),
});

export const ErrorResponseSchema = z.object({
  detail: z.string(),
});
