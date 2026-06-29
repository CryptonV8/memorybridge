import { z } from 'zod';
import { AlertSchema, RoutineSchema, AuditEventSchema } from '../lib/api-schemas';

describe('API Schemas Regression Tests', () => {
  describe('AlertSchema', () => {
    it('parses correctly with missing or null nullable fields', () => {
      const validAlertWithMissing = {
        id: 'a-1',
        caregiver_user_id: 'cg-1',
        message: 'Help needed',
        status: 'unread',
      };
      
      const parsed = AlertSchema.parse(validAlertWithMissing);
      expect(parsed.id).toBe('a-1');
      expect(parsed.created_at).toBeUndefined();

      const validAlertWithNulls = {
        id: 'a-2',
        caregiver_user_id: 'cg-1',
        message: 'Missed',
        status: 'unread',
        created_at: null,
      };

      const parsedNulls = AlertSchema.parse(validAlertWithNulls);
      expect(parsedNulls.created_at).toBeNull();
    });

    it('rejects malformed status with understandable error', () => {
      const invalidAlert = {
        id: 'a-3',
        caregiver_user_id: 'cg-1',
        message: 'Something',
        status: 'invalid_status',
      };

      const result = AlertSchema.safeParse(invalidAlert);
      expect(result.success).toBe(false);
      if (!result.success) {
        expect(result.error.issues[0].message).toMatch(/Invalid option/);
      }
    });
  });

  describe('RoutineSchema', () => {
    it('parses timestamps as strings or null', () => {
      const validRoutine = {
        id: 'r-1',
        assisted_user_id: 'au-1',
        title: 'Routine 1',
        purpose: null,
        scheduled_time: '10:00',
        timezone: 'UTC',
        steps_json: ['Step 1'],
        risk_level: 'low',
        safety_decision: 'allow_for_review',
        approval_status: 'pending',
        status: 'draft',
        created_at: '2023-10-10T10:00:00Z',
        approved_at: null,
      };

      const parsed = RoutineSchema.parse(validRoutine);
      expect(parsed.created_at).toBe('2023-10-10T10:00:00Z');
      expect(parsed.approved_at).toBeNull();
    });
  });

  describe('AuditEventSchema', () => {
    it('coerces numeric integration IDs to strings', () => {
      const auditEventWithNumericId = {
        id: 12345, // numeric ID
        correlation_id: 'corr-1',
        tool_name: 'test',
        event_type: 'event',
        decision: 'allowed',
        metadata: {},
        created_at: '2023-10-10T10:00:00Z',
      };

      const parsed = AuditEventSchema.parse(auditEventWithNumericId);
      expect(parsed.id).toBe('12345');
      expect(typeof parsed.id).toBe('string');
    });

    it('handles string integration IDs natively', () => {
      const auditEventWithStringId = {
        id: 'abc-123',
        correlation_id: 'corr-1',
        tool_name: 'test',
        event_type: 'event',
        decision: 'allowed',
        metadata: {},
        created_at: '2023-10-10T10:00:00Z',
      };

      const parsed = AuditEventSchema.parse(auditEventWithStringId);
      expect(parsed.id).toBe('abc-123');
    });
  });
});
