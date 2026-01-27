// Components/admin/admin-monitoring/admin-monitoring.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminService, SystemPerformance, SystemUsage, ApiError, ApiErrorStats } from '../../../Service/admin.service';
import { NotificationService } from '../../../Services/notification.service';

@Component({
  selector: 'app-admin-monitoring',
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-monitoring.component.html',
  styleUrl: './admin-monitoring.component.css',
})
export class AdminMonitoringComponent implements OnInit {
  private adminService = inject(AdminService);
  private notificationService = inject(NotificationService);
  
  loading = true;
  error: string | null = null;
  performance: SystemPerformance | null = null;
  usage: SystemUsage | null = null;
  selectedDays = 30;
  
  // API Errors
  apiErrors: ApiError[] = [];
  errorStats: ApiErrorStats | null = null;
  showResolvedErrors = false;
  loadingErrors = false;

  ngOnInit() {
    this.loadData();
    // Refresh every 30 seconds
    setInterval(() => {
      this.loadPerformance();
      this.loadApiErrors();
    }, 30000);
  }

  loadData() {
    this.loadPerformance();
    this.loadUsage();
    this.loadApiErrors();
    this.loadErrorStats();
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

  loadApiErrors() {
    this.loadingErrors = true;
    this.adminService.getApiErrors(50, this.showResolvedErrors ? undefined : false).subscribe({
      next: (response) => {
        this.apiErrors = response.errors;
        this.loadingErrors = false;
        
        // Show notification for critical errors
        const unresolvedCritical = this.apiErrors.filter(
          e => !e.resolved && e.error_type.includes('QUOTA')
        );
        if (unresolvedCritical.length > 0) {
          this.notificationService.error(
            'Critical API Errors',
            `${unresolvedCritical.length} unresolved Gemini API quota errors detected!`,
            0 // Persistent
          );
        }
      },
      error: (err) => {
        console.error('Error loading API errors:', err);
        this.loadingErrors = false;
      },
    });
  }

  loadErrorStats() {
    this.adminService.getApiErrorStats().subscribe({
      next: (response) => {
        this.errorStats = response.stats;
      },
      error: (err) => {
        console.error('Error loading error stats:', err);
      },
    });
  }

  resolveError(errorId: string) {
    this.adminService.resolveApiError(errorId).subscribe({
      next: () => {
        this.notificationService.success('Success', 'Error marked as resolved');
        this.loadApiErrors();
        this.loadErrorStats();
      },
      error: (err) => {
        const error = this.notificationService.parseHttpError(err);
        this.notificationService.error(error.title, error.message);
      },
    });
  }

  toggleShowResolved() {
    this.showResolvedErrors = !this.showResolvedErrors;
    this.loadApiErrors();
  }

  getErrorSeverity(errorType: string): 'critical' | 'warning' | 'info' {
    if (errorType.includes('QUOTA') || errorType.includes('EXHAUSTED')) {
      return 'critical';
    }
    if (errorType.includes('TIMEOUT') || errorType.includes('RATE_LIMIT')) {
      return 'warning';
    }
    return 'info';
  }

  getErrorBadgeClass(errorType: string): string {
    const severity = this.getErrorSeverity(errorType);
    if (severity === 'critical') return 'bg-red-100 text-red-800';
    if (severity === 'warning') return 'bg-yellow-100 text-yellow-800';
    return 'bg-blue-100 text-blue-800';
  }
}

