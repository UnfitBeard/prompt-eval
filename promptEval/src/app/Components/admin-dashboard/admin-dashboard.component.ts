import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Delta = { value: number; sign: 'up' | 'down' };
type Kpi = {
  label: string;
  value: string;
  sub?: string;
  delta: Delta;
  icon: 'users' | 'new' | 'retention' | 'time';
};

type Series = { name: string; values: number[]; color: string };
type LineChart = {
  labels: string[];
  max: number;
  series: Series[];
  w: number;
  h: number;
  pad: number;
};

type BarChart = {
  labels: string[];
  values: number[];
  max: number;
  w: number;
  h: number;
  pad: number;
  color: string;
};

type DonutSlice = { label: string; value: number; color: string };
type Donut = { slices: DonutSlice[]; radius: number; stroke: number };

type Stat = { label: string; value: string };
type HealthItem = {
  label: string;
  status: 'Operational' | 'Degraded' | 'Down' | 'Warning';
};

type UserRow = {
  id: string;
  name: string;
  joined: string;
  lastActive: string;
  prompts: number;
  avgScore: number;
  plan: 'Free' | 'Pro' | 'Enterprise';
};

@Component({
  selector: 'app-admin-dashboard',
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-dashboard.component.html',
  styleUrl: './admin-dashboard.component.css',
})
export class AdminDashboardComponent {
  // ===== KPIs =====
  kpis: Kpi[] = [
    {
      label: 'Active Users',
      value: '8,742',
      delta: { value: 11, sign: 'up' },
      icon: 'users',
    },
    {
      label: 'Beta Users (This Month)',
      value: '324',
      delta: { value: 7, sign: 'up' },
      icon: 'new',
    },
    {
      label: 'User Retention Rate',
      value: '76%',
      delta: { value: 5, sign: 'up' },
      icon: 'retention',
    },
    {
      label: 'Avg Session Duration',
      value: '12m 36s',
      delta: { value: 8, sign: 'up' },
      icon: 'time',
    },
  ];

  // ===== ML Model Performance (multi-line) =====
  modelPerf: LineChart = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May'],
    max: 100,
    w: 360,
    h: 200,
    pad: 28,
    series: [
      { name: 'clarity', values: [72, 74, 78, 81, 83], color: '#3B82F6' },
      { name: 'relevance', values: [68, 70, 75, 79, 82], color: '#10B981' },
      { name: 'specificity', values: [60, 66, 69, 73, 75], color: '#F59E0B' },
      { name: 'creativity', values: [62, 64, 67, 70, 72], color: '#8B5CF6' },
      { name: 'accuracy', values: [70, 72, 76, 80, 84], color: '#EF4444' },
    ],
  };

  // ===== User Activity (bars) =====
  activity: BarChart = {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
    values: [1200, 1800, 2600, 4100, 3900, 4800, 5100],
    max: 6000,
    w: 360,
    h: 200,
    pad: 28,
    color: '#3B82F6',
  };

  // ===== Demographics (donut) =====
  demographics: Donut = {
    slices: [
      { label: 'Mobile', value: 62, color: '#3B82F6' },
      { label: 'Web', value: 28, color: '#10B981' },
      { label: 'Desktop', value: 10, color: '#F59E0B' },
    ],
    radius: 64,
    stroke: 14,
  };

  // ===== Prompt Analysis & System Health =====
  promptStats: Stat[] = [
    { label: 'Average Prompt Length', value: '127 chars' },
    { label: 'Success Rate', value: '89%' },
    { label: 'Response Time', value: '1.2s' },
    { label: 'Error Rate', value: '1.3%' },
  ];

  systemHealth: HealthItem[] = [
    { label: 'Server Uptime', status: 'Operational' },
    { label: 'Database', status: 'Operational' },
    { label: 'Queue Workers', status: 'Warning' },
    { label: 'Active Alerts: 2', status: 'Degraded' },
  ];

  // ===== User Data table =====
  users: UserRow[] = [
    {
      id: '001',
      name: 'Sarah Chen',
      joined: '2024-01-15',
      lastActive: '2024-01-19',
      prompts: 98,
      avgScore: 9.2,
      plan: 'Pro',
    },
    {
      id: '002',
      name: 'Mike Johnson',
      joined: '2024-01-10',
      lastActive: '2024-01-18',
      prompts: 72,
      avgScore: 8.7,
      plan: 'Free',
    },
    {
      id: '003',
      name: 'Alex Kim',
      joined: '2024-01-08',
      lastActive: '2024-01-17',
      prompts: 65,
      avgScore: 8.9,
      plan: 'Pro',
    },
    {
      id: '004',
      name: 'Emma Davis',
      joined: '2024-01-05',
      lastActive: '2024-01-16',
      prompts: 58,
      avgScore: 8.5,
      plan: 'Pro',
    },
    {
      id: '005',
      name: 'James Wilson',
      joined: '2024-01-01',
      lastActive: '2024-01-14',
      prompts: 45,
      avgScore: 8.1,
      plan: 'Free',
    },
    {
      id: '006',
      name: 'David Brown',
      joined: '2023-12-28',
      lastActive: '2024-01-12',
      prompts: 38,
      avgScore: 7.9,
      plan: 'Free',
    },
  ];

  // ===== helpers =====
  deltaClass(d: Delta) {
    return d.sign === 'up' ? 'text-emerald-600' : 'text-red-600';
  }
  deltaPrefix(d: Delta) {
    return d.sign === 'up' ? '+' : '−';
  }

  initials(name: string, max = 2): string {
    return (name || '')
      .trim()
      .split(/\s+/)
      .map((w) => w[0] ?? '')
      .join('')
      .slice(0, max)
      .toUpperCase();
  }

  // line paths
  linePath(
    values: number[],
    max: number,
    w: number,
    h: number,
    pad: number
  ): string {
    const innerW = w - pad * 2,
      innerH = h - pad * 2;
    const stepX = innerW / (values.length - 1);
    return values
      .map((v, i) => {
        const x = pad + i * stepX;
        const y = pad + innerH - (v / max) * innerH;
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }
  xTick(index: number, total: number, w: number, pad: number): number {
    const innerW = w - pad * 2;
    return pad + (innerW / (total - 1)) * index;
  }

  // donut helpers
  donutCircumference(r: number) {
    return 2 * Math.PI * r;
  }
  donutOffset(percentBefore: number, r: number) {
    return this.donutCircumference(r) * (1 - percentBefore / 100);
  }
  donutPct(slice: DonutSlice, total: number) {
    return (slice.value / total) * 100;
  }
  donutTotal(): number {
    return this.demographics.slices.reduce((s, x) => s + x.value, 0);
  }
  // Total once (getter so change detection stays simple)
  get donutTotalValue(): number {
    return this.demographics.slices.reduce((sum, s) => sum + s.value, 0);
  }

  // % of circle covered before slice at index i (0..100)
  cumulativePercentBefore(i: number): number {
    const total = this.donutTotalValue || 1;
    let pct = 0;
    for (let k = 0; k < i; k++) {
      pct += (this.demographics.slices[k].value / total) * 100;
    }
    return pct;
  }

  // stroke-dashoffset value for slice i
  donutDashoffsetFor(i: number): number {
    const r = this.demographics.radius;
    const circumference = 2 * Math.PI * r;
    return circumference * (1 - this.cumulativePercentBefore(i) / 100);
  }

  // (optional) dasharray for slice i
  donutDasharrayFor(i: number): string {
    const r = this.demographics.radius;
    const circumference = 2 * Math.PI * r;
    const pct =
      (this.demographics.slices[i].value / this.donutTotalValue) * 100;
    return `${(pct / 100) * circumference} ${circumference}`;
  }
}
