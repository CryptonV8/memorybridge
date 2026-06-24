// Mock actions before they can import Next.js server components / cache headers
jest.mock('@/app/login/actions', () => ({
  login: jest.fn(),
}));
jest.mock('@/app/caregiver/routines/[routineId]/actions', () => ({
  approveDraft: jest.fn(),
  rejectDraft: jest.fn(),
  editDraft: jest.fn(),
}));

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { axe } from 'jest-axe';
import LoginPage from '@/app/login/page';
import CaregiverDashboard from '@/app/caregiver/page';
import RoutineDetailsPage from '@/app/caregiver/routines/[routineId]/page';
import { listRoutines, getAlerts, getRoutine } from '@/lib/api-client';

// Mock the API client
jest.mock('@/lib/api-client', () => ({
  listRoutines: jest.fn(),
  getAlerts: jest.fn(),
  getRoutine: jest.fn(),
}));

// Mock Next.js Link since it doesn't render normally in jsdom
jest.mock('next/link', () => {
  return ({ children, href, ...rest }: { children: React.ReactNode; href: string; [key: string]: any }) => {
    return <a href={href} {...rest}>{children}</a>;
  };
});

describe('LoginPage', () => {
  it('renders login form and shows demo warning', async () => {
    const { container } = render(<LoginPage />);
    
    // Check for demo warning
    expect(screen.getByText(/demonstration environment/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Enter Demo Environment/i })).toBeInTheDocument();

    // Check accessibility
    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe('CaregiverDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders routines and alerts grouped correctly', async () => {
    (listRoutines as jest.Mock).mockResolvedValue({
      items: [
        {
          id: 'r1',
          assisted_user_id: 'au1',
          title: 'Morning Medication',
          status: 'active',
          approval_status: 'approved',
          scheduled_time: '08:00',
          timezone: 'UTC',
          steps_json: ['Take 1 blue pill'],
          risk_level: 'low',
          safety_decision: 'allow_for_review',
        },
        {
          id: 'r2',
          assisted_user_id: 'au1',
          title: 'Check Lock on Door',
          status: 'draft',
          approval_status: 'pending',
          scheduled_time: '20:00',
          timezone: 'UTC',
          steps_json: ['Go to back door', 'Turn lock lock-wise'],
          risk_level: 'medium',
          safety_decision: 'allow_for_review',
        }
      ]
    });

    (getAlerts as jest.Mock).mockResolvedValue([
      {
        id: 'a1',
        caregiver_user_id: 'cg1',
        message: 'Maria requested help',
        status: 'unread',
        priority: 'high',
        created_at: '2026-06-21T08:00:00Z',
      }
    ]);

    const dashboardJSX = await CaregiverDashboard();
    const { container } = render(dashboardJSX);

    expect(screen.getByText('Morning Medication')).toBeInTheDocument();
    expect(screen.getByText('Check Lock on Door')).toBeInTheDocument();
    expect(screen.getByText('Maria requested help')).toBeInTheDocument();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('handles backend API down state gracefully', async () => {
    (listRoutines as jest.Mock).mockRejectedValue(new Error('Network error'));
    (getAlerts as jest.Mock).mockRejectedValue(new Error('Network error'));

    const dashboardJSX = await CaregiverDashboard();
    render(dashboardJSX);

    expect(screen.getByText('API Unavailable')).toBeInTheDocument();
  });
});

describe('RoutineDetailsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders a safe routine draft with details and approval UI', async () => {
    (getRoutine as jest.Mock).mockResolvedValue({
      id: 'r-safe',
      assisted_user_id: 'au1',
      title: 'Water the plants',
      status: 'draft',
      approval_status: 'pending',
      scheduled_time: '10:00',
      timezone: 'UTC',
      steps_json: ['Water patio plants', 'Water indoor plants'],
      risk_level: 'low',
      safety_decision: 'allow_for_review',
      metadata: {
        original_instruction: 'water flowers at 10',
        visible_steps: ['Water flowers'],
        help_text: 'Use the green watering can',
      }
    });

    const pageJSX = await RoutineDetailsPage({ params: Promise.resolve({ routineId: 'r-safe' }) });
    render(pageJSX);

    await waitFor(() => {
      expect(screen.getByText('Water patio plants')).toBeInTheDocument();
    });

    expect(screen.getByText('LOW RISK')).toBeInTheDocument();
    expect(screen.getByText('"water flowers at 10"')).toBeInTheDocument();
    expect(screen.getAllByText('Water flowers')[0]).toBeInTheDocument();
    expect(screen.getByText(/"Use the green watering can"/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Approve & Activate/i })).toBeInTheDocument();
  });

  it('renders a prohibited routine draft with warnings and disabled approval', async () => {
    (getRoutine as jest.Mock).mockResolvedValue({
      id: 'r-prohibited',
      assisted_user_id: 'au1',
      title: 'Take daily medication',
      status: 'rejected',
      approval_status: 'rejected',
      scheduled_time: '09:00',
      timezone: 'UTC',
      steps_json: ['Take red pill from organizer'],
      risk_level: 'prohibited',
      safety_decision: 'reject_prohibited',
      metadata: {
        original_instruction: 'give her pills at 9am',
        policy_reasons: ['Medication routines cannot be managed automatically.'],
      }
    });

    const pageJSX = await RoutineDetailsPage({ params: Promise.resolve({ routineId: 'r-prohibited' }) });
    const { container } = render(pageJSX);

    await waitFor(() => {
      expect(screen.getByText('Take red pill from organizer')).toBeInTheDocument();
    });

    expect(screen.getByText('PROHIBITED RISK')).toBeInTheDocument();
    expect(screen.getByText('Routine Blocked by Safety Policy')).toBeInTheDocument();
    expect(screen.getAllByText('Medication routines cannot be managed automatically.')[0]).toBeInTheDocument();
    
    // Approval button should not be present
    expect(screen.queryByRole('button', { name: /Approve & Activate/i })).not.toBeInTheDocument();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

// Import the alerts page for testing
import AlertsPage from '@/app/caregiver/alerts/page';

describe('AlertsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders alerts and check accessibility', async () => {
    (getAlerts as jest.Mock).mockResolvedValue([
      {
        id: 'a-alert-1',
        caregiver_user_id: 'cg1',
        message: 'Maria requested help with: Water the plants',
        status: 'unread',
        priority: 'high',
        created_at: '2026-06-21T10:00:00Z',
      }
    ]);

    const pageJSX = await AlertsPage();
    const { container } = render(pageJSX);

    await waitFor(() => {
      expect(screen.getByText('Maria requested help with: Water the plants')).toBeInTheDocument();
    });

    expect(screen.getByText('high')).toBeInTheDocument();

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

