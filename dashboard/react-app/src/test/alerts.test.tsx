import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { AlertBadge } from '../components/AlertBadge';
import { AlertCard } from '../components/AlertCard';
import { ActiveAlertsPanel } from '../components/ActiveAlertsPanel';
import { AlertItem } from '../types';

describe('Alerts UI Components', () => {
  const sampleAlert: AlertItem = {
    alert_id: 'alt-101',
    rule_id: 'PUMP_VIBRATION_CRITICAL',
    machine_id: 'PMP-001',
    machine_type: 'PUMP',
    alert_code: 'VIB_CRITICAL',
    severity: 'CRITICAL',
    title: 'Pump High Vibration',
    description: 'vibration_x_mm_s exceeded 8.0 mm/s',
    status: 'OPEN',
    triggered_at: '2026-09-29T10:00:00Z',
    occurrence_count: 3,
    triggering_measurements: { vibration_x_mm_s: 9.42 },
    current_measurements: { vibration_x_mm_s: 9.85 },
  };

  it('renders AlertBadge correctly with severity levels', () => {
    const { rerender } = render(<AlertBadge severity="CRITICAL" />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();

    rerender(<AlertBadge severity="WARNING" />);
    expect(screen.getByText('WARNING')).toBeInTheDocument();

    rerender(<AlertBadge severity="INFO" />);
    expect(screen.getByText('INFO')).toBeInTheDocument();
  });

  it('renders AlertCard with telemetry details and handles acknowledge action', () => {
    const onAck = vi.fn();
    const onResolve = vi.fn();

    render(
      <BrowserRouter>
        <AlertCard alert={sampleAlert} onAcknowledge={onAck} onResolve={onResolve} />
      </BrowserRouter>
    );

    expect(screen.getByText('Pump High Vibration')).toBeInTheDocument();
    expect(screen.getByText('PMP-001')).toBeInTheDocument();
    expect(screen.getByText('vibration_x_mm_s:')).toBeInTheDocument();
    expect(screen.getByText('9.42')).toBeInTheDocument();

    const ackBtn = screen.getByRole('button', { name: /acknowledge/i });
    fireEvent.click(ackBtn);
    expect(onAck).toHaveBeenCalledWith('alt-101');
  });

  it('renders ActiveAlertsPanel with multiple alerts', () => {
    render(
      <BrowserRouter>
        <ActiveAlertsPanel alerts={[sampleAlert]} />
      </BrowserRouter>
    );
    expect(screen.getByText('Active Operational Alerts (1)')).toBeInTheDocument();
    expect(screen.getByText('Pump High Vibration')).toBeInTheDocument();
  });

  it('renders ActiveAlertsPanel empty state when no active alerts', () => {
    render(<ActiveAlertsPanel alerts={[]} />);
    expect(screen.getByText('All Systems Operating Normally')).toBeInTheDocument();
  });
});
