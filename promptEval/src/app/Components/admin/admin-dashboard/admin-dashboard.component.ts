import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminService, DashboardStats } from '../../../Service/admin.service';

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
export class AdminDashboardComponent implements OnInit {
  private adminService = inject(AdminService);
  loading = true;
  error: string | null = null;

  // ===== KPIs =====
  kpis: Kpi[] = [];

  // ===== ML Model Performance (multi-line) =====
  modelPerf: LineChart = {
    labels: [],
    max: 10,
    w: 360,
    h: 200,
    pad: 28,
    series: [],
  };

  // ===== User Activity (bars) =====
  activity: BarChart = {
    labels: [],
    values: [],
    max: 100,
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
  promptStats: Stat[] = [];
  systemHealth: HealthItem[] = [];

  // ===== User Data table =====
  users: UserRow[] = [];

  ngOnInit() {
    this.loadDashboardStats();
  }

  loadDashboardStats() {
    this.loading = true;
    this.error = null;

    this.adminService.getDashboardStats().subscribe({
      next: (stats: DashboardStats) => {
        this.updateKPIs(stats.kpis);
        this.updateModelPerformance(stats.model_performance);
        this.updateUserActivity(stats.user_activity);
        this.updatePromptStats(stats.prompt_statistics);
        this.systemHealth = stats.system_health.map((h) => ({
          label: h.label,
          status: h.status,
        }));
        this.users = stats.top_users.map((u) => ({
          id: u.id,
          name: u.name,
          joined: u.joined,
          lastActive: u.lastActive,
          prompts: u.prompts,
          avgScore: u.avgScore,
          plan: u.plan as 'Free' | 'Pro' | 'Enterprise',
        }));
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading dashboard stats:', err);
        this.error = 'Failed to load dashboard statistics';
        this.loading = false;
      },
    });
  }

  private updateKPIs(kpis: DashboardStats['kpis']) {
    this.kpis = [
      {
        label: 'Active Users',
        value: kpis.active_users.toLocaleString(),
        delta: {
          value: Math.abs(kpis.new_users_delta),
          sign: kpis.new_users_delta >= 0 ? 'up' : 'down',
        },
        icon: 'users',
      },
      {
        label: 'New Users (This Month)',
        value: kpis.new_users_this_month.toLocaleString(),
        delta: {
          value: Math.abs(kpis.new_users_delta),
          sign: kpis.new_users_delta >= 0 ? 'up' : 'down',
        },
        icon: 'new',
      },
      {
        label: 'User Retention Rate',
        value: `${kpis.retention_rate.toFixed(1)}%`,
        delta: { value: 5, sign: 'up' }, // TODO: Calculate actual delta
        icon: 'retention',
      },
      {
        label: 'Avg Session Duration',
        value: kpis.avg_session_duration,
        delta: { value: 8, sign: 'up' }, // TODO: Calculate actual delta
        icon: 'time',
      },
    ];
  }

  private updateModelPerformance(perf: DashboardStats['model_performance']) {
    this.modelPerf = {
      labels: perf.labels,
      max: 10,
      w: 360,
      h: 200,
      pad: 28,
      series: perf.series.map((s) => ({
        name: s.name,
        values: s.values,
        color: s.color,
      })),
    };
  }

  private updateUserActivity(activity: DashboardStats['user_activity']) {
    const maxValue = Math.max(...activity.values, 1);
    this.activity = {
      labels: activity.labels,
      values: activity.values,
      max: Math.ceil(maxValue * 1.2), // Add 20% padding
      w: 360,
      h: 200,
      pad: 28,
      color: '#3B82F6',
    };
  }

  private updatePromptStats(stats: DashboardStats['prompt_statistics']) {
    this.promptStats = [
      {
        label: 'Average Prompt Length',
        value: `${stats.average_prompt_length} chars`,
      },
      {
        label: 'Success Rate',
        value: `${stats.success_rate.toFixed(1)}%`,
      },
      {
        label: 'Response Time',
        value: `${stats.response_time.toFixed(1)}s`,
      },
      {
        label: 'Error Rate',
        value: `${stats.error_rate.toFixed(1)}%`,
      },
    ];
  }

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
