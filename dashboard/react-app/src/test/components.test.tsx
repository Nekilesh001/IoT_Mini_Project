import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect } from 'vitest';
import { StateBadge } from '../components/StateBadge';
import { QualityBadge } from '../components/QualityBadge';
import { ProtocolBadge } from '../components/ProtocolBadge';
import { MetricCard } from '../components/MetricCard';
import { MachineCard } from '../components/MachineCard';
import { MachineOverviewItem } from '../types';

describe('Frontend UI Components', () => {
  it('renders StateBadge with correct status color and accessible label', () => {
    render(<StateBadge state="RUNNING" />);
    expect(screen.getByTestId('state-badge-RUNNING')).toHaveTextContent('RUNNING');
  });

  it('renders QualityBadge correctly', () => {
    render(<QualityBadge quality="GOOD" />);
    expect(screen.getByTestId('quality-badge-GOOD')).toHaveTextContent('QUALITY: GOOD');
  });

  it('renders ProtocolBadge correctly', () => {
    render(<ProtocolBadge protocol="OPC_UA" />);
    expect(screen.getByTestId('protocol-badge-OPC_UA')).toHaveTextContent('OPC_UA');
  });

  it('renders MetricCard with formatted numerical values and units', () => {
    render(<MetricCard label="spindle_speed_rpm" value={9200.5} unit="RPM" />);
    expect(screen.getByText('SPINDLE SPEED RPM')).toBeInTheDocument();
    expect(screen.getByText('9200.50')).toBeInTheDocument();
    expect(screen.getByText('RPM')).toBeInTheDocument();
  });

  it('renders MachineCard with machine-specific measurements', () => {
    const mockMachine: MachineOverviewItem = {
      machine_id: 'CNC-001',
      machine_type: 'CNC_MACHINING_CENTER',
      protocol: 'OPC_UA',
      plant_id: 'PLANT_01',
      line_id: 'LINE_A',
      operating_state: 'RUNNING',
      health_state: 'HEALTHY',
      quality: 'GOOD',
      sequence: 42,
      latest_event_time: '2026-09-29T10:00:00Z',
      key_measurements: {
        spindle_speed_rpm: 9200.0,
        vibration_rms_mm_s: 0.85,
      },
    };

    render(
      <BrowserRouter>
        <MachineCard machine={mockMachine} />
      </BrowserRouter>
    );

    expect(screen.getByText('CNC-001')).toBeInTheDocument();
    expect(screen.getByText('CNC MACHINING CENTER')).toBeInTheDocument();
    expect(screen.getByText('Seq #42')).toBeInTheDocument();
    expect(screen.getByText('9200')).toBeInTheDocument();
  });
});
