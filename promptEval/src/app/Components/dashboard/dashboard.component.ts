import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

type Delta = { value: number; sign: 'up' | 'down' };
type Metric = { label: string; value: string; sub?: string; delta: Delta };

type WeeklyActivity = {
  days: string[];
  prompts: number[]; // e.g., 0..20
  score: number[]; // e.g., 0..12 (secondary axis)
  maxPrompts: number;
  maxScore: number;
};

type RadarData = {
  categories: string[];
  values: number[]; // 0..10
  max: number; // 10
};

type Achievement = {
  title: string;
  date: string;
  icon: 'trophy' | 'bolt' | 'medal' | 'target' | 'spark';
  progressPct?: number;
};

type UsedTemplate = { name: string; used: number };

type Performer = {
  rank: number;
  name: string;
  score: number;
  progressPct: number;
  change: number;
};

@Component({
  selector: 'app-dashboard',
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent {
  // ======== KPI METRICS ========
  metrics: Metric[] = [
    { label: 'Total Prompts', value: '847', delta: { value: 12, sign: 'up' } },
    {
      label: 'Average Score',
      value: '8.7/10',
      delta: { value: 5, sign: 'up' },
    },
    {
      label: 'Current Streak',
      value: '12 Days',
      delta: { value: 3, sign: 'up' },
    },
    {
      label: 'Time Invested',
      value: '127 Hours',
      delta: { value: 8, sign: 'up' },
    },
  ];

  // ======== RADAR (Score by Category) ========
  radar: RadarData = {
    categories: ['Clarity', 'Tone', 'Structure', 'Creativity', 'Technical'],
    values: [8.8, 7.9, 8.4, 8.1, 7.3],
    max: 10,
  };

  // SVG sizing for radar
  radarSize = 280;
  radarPadding = 24; // space for labels
  radarRings = [2, 4, 6, 8, 10]; // grid levels

  // ======== WEEKLY ACTIVITY (line chart) ========
  weekly: WeeklyActivity = {
    days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
    prompts: [14, 13, 12, 19, 15, 16, 14],
    score: [10, 10, 9, 11.5, 10.5, 11, 9.5],
    maxPrompts: 20,
    maxScore: 12,
  };
  lineW = 280;
  lineH = 160;
  linePad = 24;

  // ======== ACHIEVEMENTS ========
  achievements: Achievement[] = [
    {
      title: 'Clarity Champion',
      date: '2024-01-15',
      icon: 'trophy',
      progressPct: 85,
    },
    {
      title: '50 Prompts Milestone',
      date: '2024-01-10',
      icon: 'medal',
      progressPct: 66,
    },
    {
      title: 'Perfect Week',
      date: '2024-01-05',
      icon: 'target',
      progressPct: 100,
    },
    {
      title: 'Template Master',
      date: '2024-01-01',
      icon: 'trophy',
      progressPct: 90,
    },
    {
      title: 'Quick Learner',
      date: '2023-12-28',
      icon: 'bolt',
      progressPct: 72,
    },
    {
      title: 'Consistency King',
      date: '2023-12-25',
      icon: 'spark',
      progressPct: 88,
    },
  ];

  // ======== MOST USED TEMPLATES (horizontal bars) ========
  usedTemplates: UsedTemplate[] = [
    { name: 'Creative Writing', used: 135 },
    { name: 'Technical Documentation', used: 108 },
    { name: 'Marketing Copy', used: 78 },
    { name: 'Social Media', used: 52 },
    { name: 'Email Communication', used: 40 },
  ];
  get usedMax(): number {
    return Math.max(...this.usedTemplates.map((t) => t.used));
  }
  widthPct(v: number): string {
    return `${Math.round((v / this.usedMax) * 100)}%`;
  }

  // ======== TOP PERFORMERS ========
  performers: Performer[] = [
    { rank: 1, name: 'Sarah Chen', score: 98.5, progressPct: 72, change: +2 },
    { rank: 2, name: 'Mike Johnson', score: 97.2, progressPct: 60, change: -1 },
    { rank: 3, name: 'Alex Kim', score: 96.8, progressPct: 64, change: +1 },
    { rank: 4, name: 'Emma Davis', score: 95.4, progressPct: 58, change: 0 },
    { rank: 5, name: 'James Wilson', score: 94.9, progressPct: 62, change: -2 },
  ];

  // ======== RADAR helpers ========
  private toRad(deg: number) {
    return (deg * Math.PI) / 180;
  }
  private center(): { cx: number; cy: number; r: number } {
    const r = this.radarSize / 2 - this.radarPadding;
    return { cx: this.radarSize / 2, cy: this.radarSize / 2, r };
  }

  initials(name: string, max = 2): string {
    if (!name) return '';
    return name
      .trim()
      .split(/\s+/) // split on spaces
      .map((w) => w[0] ?? '') // first letter of each word
      .join('')
      .slice(0, max)
      .toUpperCase();
  }

  radarPolygon(points: number[]): string {
    const { cx, cy, r } = this.center();
    const n = this.radar.categories.length;
    return points
      .map((v, i) => {
        const angle = this.toRad((360 / n) * i - 90); // start at top
        const radius = (v / this.radar.max) * r;
        const x = cx + Math.cos(angle) * radius;
        const y = cy + Math.sin(angle) * radius;
        return `${x},${y}`;
      })
      .join(' ');
  }

  radarGrid(level: number): string {
    // polygon for grid ring at a particular value (e.g., 2/10, 4/10)
    const vals = Array(this.radar.categories.length).fill(level);
    return this.radarPolygon(vals);
  }

  radarAxis(i: number): { x2: number; y2: number } {
    const { cx, cy, r } = this.center();
    const n = this.radar.categories.length;
    const angle = this.toRad((360 / n) * i - 90);
    return { x2: cx + Math.cos(angle) * r, y2: cy + Math.sin(angle) * r };
  }

  radarLabel(i: number): {
    x: number;
    y: number;
    anchor: 'start' | 'middle' | 'end';
  } {
    const { cx, cy, r } = this.center();
    const n = this.radar.categories.length;
    const angle = this.toRad((360 / n) * i - 90);
    const offset = 18;
    const x = cx + Math.cos(angle) * (r + offset);
    const y = cy + Math.sin(angle) * (r + offset);
    const cos = Math.cos(angle);
    let anchor: 'start' | 'middle' | 'end' = 'middle';
    if (cos > 0.2) anchor = 'start';
    else if (cos < -0.2) anchor = 'end';
    return { x, y, anchor };
  }

  // ======== LINE helpers (weekly activity) ========
  linePath(values: number[], max: number): string {
    const w = this.lineW,
      h = this.lineH,
      p = this.linePad;
    const innerW = w - p * 2,
      innerH = h - p * 2;
    const stepX = innerW / (values.length - 1);
    return values
      .map((v, i) => {
        const x = p + stepX * i;
        const y = p + innerH - (v / max) * innerH;
        return `${i === 0 ? 'M' : 'L'} ${x} ${y}`;
      })
      .join(' ');
  }

  xTick(i: number): number {
    const w = this.lineW,
      p = this.linePad;
    const innerW = w - p * 2;
    const stepX = innerW / (this.weekly.days.length - 1);
    return p + stepX * i;
  }

  // color helpers
  deltaColor(d: Delta) {
    return d.sign === 'up' ? 'text-emerald-600' : 'text-red-600';
  }
  deltaPrefix(d: Delta) {
    return d.sign === 'up' ? '+' : '−';
  }
}
