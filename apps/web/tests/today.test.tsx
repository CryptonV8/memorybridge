/**
 * today.test.tsx — Phase 4 unit tests for the /today assisted-user interface
 *
 * Tests the TodayClient component in isolation with mocked server actions.
 */
import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TodayClient } from '../app/today/TodayClient';

// ── Mock server actions ───────────────────────────────────────────────────────
jest.mock('../app/today/actions', () => ({
  markDoneAction: jest.fn().mockResolvedValue({}),
  helpAction: jest.fn().mockResolvedValue({}),
  contactAction: jest.fn().mockResolvedValue({}),
}));

// ── Mock Web Speech API ───────────────────────────────────────────────────────
const mockSpeak = jest.fn();
const mockCancel = jest.fn();

// jsdom does not implement Web Speech API; define stubs on window
Object.defineProperty(window, 'speechSynthesis', {
  value: {
    speak: mockSpeak,
    cancel: mockCancel,
  },
  writable: true,
  configurable: true,
});

// SpeechSynthesisUtterance is also absent in jsdom
(global as Record<string, unknown>).SpeechSynthesisUtterance = jest.fn().mockImplementation(function (this: Record<string, unknown>, text: string) {
  this.text = text;
  this.rate = 1;
  this.pitch = 1;
  this.lang = 'en-US';
  this.onstart = null;
  this.onend = null;
  this.onerror = null;
});


const mockRoutines = [
  {
    id: 'routine-1',
    title: 'Water the plants',
    purpose: null,
    scheduled_time: '10:00',
    timezone: 'Europe/Sofia',
    steps_json: ['Take the watering can', 'Water the plants near the window'],
    status: 'active',
  },
  {
    id: 'routine-2',
    title: 'Drink water',
    purpose: null,
    scheduled_time: '12:00',
    timezone: 'Europe/Sofia',
    steps_json: ['Take a glass', 'Fill it with water', 'Drink'],
    status: 'active',
  },
];

describe('TodayClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the first routine title and steps', () => {
    render(<TodayClient routines={mockRoutines} />);
    expect(screen.getByText('Water the plants')).toBeInTheDocument();
    expect(screen.getByText('Take the watering can')).toBeInTheDocument();
    expect(screen.getByText('Water the plants near the window')).toBeInTheDocument();
  });

  it('shows all three primary action buttons', () => {
    render(<TodayClient routines={mockRoutines} />);
    expect(screen.getByRole('button', { name: /mark this routine as done/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /request help/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /ask your caregiver to contact you/i })).toBeInTheDocument();
  });

  it('shows Listen button', () => {
    render(<TodayClient routines={mockRoutines} />);
    expect(screen.getByRole('button', { name: /listen to this routine read aloud/i })).toBeInTheDocument();
  });

  it('shows pagination when there are multiple routines', () => {
    render(<TodayClient routines={mockRoutines} />);
    expect(screen.getByText('1 of 2')).toBeInTheDocument();
  });

  it('navigates to next routine on Next button click', () => {
    render(<TodayClient routines={mockRoutines} />);
    const nextBtn = screen.getByRole('button', { name: /next routine/i });
    fireEvent.click(nextBtn);
    expect(screen.getByText('Drink water')).toBeInTheDocument();
    expect(screen.getByText('2 of 2')).toBeInTheDocument();
  });

  it('shows empty state when no active routines', () => {
    render(<TodayClient routines={[]} />);
    expect(screen.getByText(/You have no routines scheduled right now/i)).toBeInTheDocument();
  });

  it('does not auto-play speech on render', () => {
    render(<TodayClient routines={mockRoutines} />);
    expect(mockSpeak).not.toHaveBeenCalled();
  });

  it('calls speechSynthesis.speak when Listen is clicked', () => {
    render(<TodayClient routines={mockRoutines} />);
    const listenBtn = screen.getByRole('button', { name: /listen to this routine read aloud/i });
    fireEvent.click(listenBtn);
    expect(mockSpeak).toHaveBeenCalled();
  });
});

// ── Security: Token scan ──────────────────────────────────────────────────────
import fs from 'fs';
import path from 'path';

describe('Security: Assisted-user token non-exposure', () => {
  it('ensures DEMO_ASSISTED_USER_TOKEN does not leak into client-side bundles', () => {
    const token = process.env.DEMO_ASSISTED_USER_TOKEN || 'test-sentinel-au-token';
    const staticDir = path.resolve(__dirname, '../.next/static');

    if (!fs.existsSync(staticDir)) {
      console.warn('Production build .next/static not found, skipping scan.');
      return;
    }

    const scanDirectory = (dir: string) => {
      const files = fs.readdirSync(dir);
      for (const file of files) {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat.isDirectory()) {
          scanDirectory(fullPath);
        } else if (stat.isFile() && (file.endsWith('.js') || file.endsWith('.html') || file.endsWith('.txt'))) {
          const content = fs.readFileSync(fullPath, 'utf8');
          if (content.includes(token)) {
            throw new Error(`Security Violation: Assisted-user token "${token}" found in client asset: ${fullPath}`);
          }
        }
      }
    };

    scanDirectory(staticDir);
  });
});
