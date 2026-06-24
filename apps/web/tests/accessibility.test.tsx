/**
 * accessibility.test.tsx — Phase 5 axe-core accessibility scans
 *
 * Scans the caregiver RoutineDetailsClient and assisted-user TodayClient
 * for WCAG 2.1 violations using jest-axe.
 *
 * Requirements from SAFETY_POLICY.md R5:
 *   "Enforce minimum 44px targets, maximum one active task on screen,
 *    high contrast, text-to-speech. axe-core testing."
 */
import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

// ── Mocks ────────────────────────────────────────────────────────────────────
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), refresh: jest.fn() }),
  useParams: () => ({ routineId: 'test-routine-id' }),
  redirect: jest.fn(),
}));

jest.mock('@/app/caregiver/routines/[routineId]/actions', () => ({
  approveRoutineAction: jest.fn(),
  rejectRoutineAction: jest.fn(),
}), { virtual: true });

jest.mock('@/app/today/actions', () => ({
  markCompleted: jest.fn(),
  requestHelp: jest.fn(),
  requestContact: jest.fn(),
}), { virtual: true });

// ── Fixture data ──────────────────────────────────────────────────────────────
const mockAllowedRoutine = {
  id: 'r-test-allowed',
  title: 'Water the plants',
  purpose: 'Morning routine',
  scheduled_time: '10:00',
  timezone: 'Europe/Sofia',
  steps_json: ['Take the watering can.', 'Water the plants near the window.'],
  risk_level: 'low',
  safety_decision: 'allow_for_review',
  status: 'draft',
  approval_status: 'pending',
  created_at: '2026-06-23T08:00:00Z',
  approved_at: null,
  metadata_json: {
    visible_steps: ['Take the watering can.', 'Water the plants near the window.'],
    help_text: 'Press Help me if you need assistance.',
    policy_reasons: ['Passed all safety checks.'],
    original_instruction: 'Remind Maria at 10:00 to water the plants.',
    missing_information: [],
  },
};

const mockTodayRoutine = {
  id: 'r-today-1',
  title: 'Water the plants',
  scheduled_time: '10:00',
  steps_json: ['Take the watering can.', 'Water the plants near the window.'],
  visible_steps: ['Take the watering can.', 'Water the plants near the window.'],
  help_text: 'Press Help me if you need assistance.',
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('Caregiver RoutineDetailsClient — Accessibility', () => {
  let RoutineDetailsClient: React.ComponentType<any>;

  beforeAll(async () => {
    // Dynamic import — both are named exports
    const mod = await import('@/app/caregiver/routines/[routineId]/RoutineDetailsClient');
    RoutineDetailsClient = mod.RoutineDetailsClient;
  });

  it('has no axe violations on draft allowed routine', async () => {
    const { container } = render(
      <RoutineDetailsClient routine={mockAllowedRoutine} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations on prohibited routine', async () => {
    const prohibitedRoutine = {
      ...mockAllowedRoutine,
      id: 'r-test-prohibited',
      title: 'Change medication',
      risk_level: 'prohibited',
      safety_decision: 'reject_prohibited',
      status: 'rejected',
      approval_status: 'rejected',
    };
    const { container } = render(
      <RoutineDetailsClient routine={prohibitedRoutine} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe('Assisted-User TodayClient — Accessibility', () => {
  let TodayClient: React.ComponentType<any>;

  beforeAll(async () => {
    const mod = await import('@/app/today/TodayClient');
    TodayClient = mod.TodayClient;
  });

  it('has no axe violations with active routine', async () => {
    const { container } = render(
      <TodayClient routines={[mockTodayRoutine]} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('has no axe violations when no routine is scheduled', async () => {
    const { container } = render(
      <TodayClient routines={[]} />
    );
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});
