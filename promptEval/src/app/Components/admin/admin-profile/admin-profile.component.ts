import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';

type InfoItem = {
  label: string;
  value: string;
  icon?: 'mail' | 'phone' | 'location' | 'team' | 'calendar' | 'id';
};
type RoleItem = { label: string; ok: boolean };
type Metric = { label: string; score: number }; // out of 5.0
type Activity = {
  date: string;
  template: string;
  action: 'Created' | 'Edited' | 'Reviewed';
  score: number;
  status: 'Done' | 'Draft' | 'Queued';
  time: string;
};

@Component({
  selector: 'app-admin-profile',
  imports: [CommonModule],
  templateUrl: './admin-profile.component.html',
  styleUrl: './admin-profile.component.css',
})
export class AdminProfileComponent {
  // ===== Header =====
  fullName = 'Njunge George Njuguna';
  title = 'Senior Prompt Engineer';

  // ===== Contact / Org cards =====
  leftInfo: InfoItem[] = [
    { label: 'Email', value: 'george.ng@prompteval.ai', icon: 'mail' },
    { label: 'Location', value: 'Nairobi, Kenya', icon: 'location' },
    { label: 'Join Date', value: 'Sep 2023', icon: 'calendar' },
  ];
  rightInfo: InfoItem[] = [
    { label: 'Phone', value: '+254 712 123 456', icon: 'phone' },
    { label: 'Department', value: 'Prompt Engineering', icon: 'team' },
    { label: 'Employee ID', value: 'AE-2023-0148', icon: 'id' },
  ];

  // ===== Roles =====
  roles: RoleItem[] = [
    { label: 'Prompt Template Management', ok: true },
    { label: 'Quality Assurance', ok: true },
    { label: 'User Support', ok: true },
    { label: 'System Administration', ok: true },
  ];

  // ===== Prompt Evaluation Metrics (out of 5) =====
  metrics: Metric[] = [
    { label: 'Overall Score', score: 4.7 },
    { label: 'Context Score', score: 4.6 },
    { label: 'Relevance Score', score: 4.8 },
    { label: 'Specificity Rating', score: 4.4 },
    { label: 'Creativity Score', score: 4.5 },
  ];
  // ring chart sizing
  ring = { r: 26, stroke: 6 }; // radius & stroke width

  // ===== Recent Activities =====
  activities: Activity[] = [
    {
      date: '2024-01-19',
      template: 'Product Description Generator',
      action: 'Edited',
      score: 9.1,
      status: 'Done',
      time: '4m',
    },
    {
      date: '2024-01-18',
      template: 'Bug Report Template',
      action: 'Created',
      score: 8.6,
      status: 'Done',
      time: '6m',
    },
    {
      date: '2024-01-16',
      template: 'Blog Post Outline Creator',
      action: 'Reviewed',
      score: 9.0,
      status: 'Done',
      time: '5m',
    },
    {
      date: '2024-01-14',
      template: 'Social Media Caption',
      action: 'Edited',
      score: 8.7,
      status: 'Done',
      time: '3m',
    },
    {
      date: '2024-01-12',
      template: 'SQL Query Generator',
      action: 'Created',
      score: 8.4,
      status: 'Done',
      time: '8m',
    },
  ];

  // ===== Helpers =====
  initials(name: string): string {
    return (name || '')
      .trim()
      .split(/\s+/)
      .map((w) => w[0] ?? '')
      .join('')
      .slice(0, 2)
      .toUpperCase();
  }

  circ(r: number) {
    return 2 * Math.PI * r;
  }
  ringDasharray(score: number): string {
    const max = 5; // out of 5
    const pct = Math.max(0, Math.min(1, score / max));
    const total = this.circ(this.ring.r);
    return `${pct * total} ${total}`;
  }
  ringOffset(): number {
    // start at top
    return this.circ(this.ring.r) * (1 - 0);
  }

  badgeColor(status: Activity['status']): string {
    return status === 'Done'
      ? 'bg-emerald-50 text-emerald-700'
      : status === 'Draft'
      ? 'bg-gray-100 text-gray-700'
      : 'bg-indigo-50 text-indigo-700';
  }
}
