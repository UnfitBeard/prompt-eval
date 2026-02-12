// Components/admin/admin-monitoring/admin-monitoring.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminService, SystemPerformance, SystemUsage } from '../../../Service/admin.service';

@Component({
  selector: 'app-admin-monitoring',
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-monitoring.component.html',
  styleUrl: './admin-monitoring.component.css',
})
export class AdminMonitoringComponent implements OnInit {
  private adminService = inject(AdminService);
  
  loading = true;
  error: string | null = null;
  performance: SystemPerformance | null = null;
  usage: SystemUsage | null = null;
  selectedDays = 30;

  ngOnInit() {
    this.loadData();
    // Refresh every 30 seconds
    setInterval(() => this.loadPerformance(), 30000);
  }

  loadData() {
    this.loadPerformance();
    this.loadUsage();
  }

  loadPerformance() {
    this.adminService.getSystemPerformance().subscribe({
      next: (perf) => {
        this.performance = perf;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading performance:', err);
        this.error = 'Failed to load system performance';
        this.loading = false;
      },
    });
  }

  loadUsage() {
    this.adminService.getSystemUsage(this.selectedDays).subscribe({
      next: (usage) => {
        this.usage = usage;
      },
      error: (err) => {
        console.error('Error loading usage:', err);
      },
    });
  }

  onDaysChange() {
    this.loadUsage();
  }

  getHealthColor(percent: number): string {
    if (percent < 50) return 'text-emerald-600';
    if (percent < 80) return 'text-yellow-600';
    return 'text-red-600';
  }

  getHealthBgColor(percent: number): string {
    if (percent < 50) return 'bg-emerald-100';
    if (percent < 80) return 'bg-yellow-100';
    return 'bg-red-100';
  }

  getMaxDailyUsage(): number {
    if (!this.usage || !this.usage.daily_usage || this.usage.daily_usage.length === 0) {
      return 1;
    }
    return Math.max(...this.usage.daily_usage.map(d => d.count), 1);
  }

  getBarHeight(dayCount: number): number {
    const max = this.getMaxDailyUsage();
    return (dayCount / max) * 100;
  }

  getDayTitle(dayCount: number, date: string): string {
    return `${dayCount} evaluations on ${date}`;
  }
}

