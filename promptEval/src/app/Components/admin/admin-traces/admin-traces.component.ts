// Components/admin/admin-traces/admin-traces.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { AdminService, EvaluationTrace, TracesResponse } from '../../../Service/admin.service';

@Component({
  selector: 'app-admin-traces',
  imports: [CommonModule],
  templateUrl: './admin-traces.component.html',
  styleUrl: './admin-traces.component.css',
})
export class AdminTracesComponent implements OnInit {
  private adminService = inject(AdminService);
  
  loading = true;
  error: string | null = null;
  traces: EvaluationTrace[] = [];
  total = 0;
  limit = 50;
  offset = 0;
  selectedTrace: EvaluationTrace | null = null;
  showDetails = false;

  ngOnInit() {
    this.loadTraces();
  }

  loadTraces() {
    this.loading = true;
    this.error = null;

    this.adminService.getEvaluationTraces(this.limit, this.offset).subscribe({
      next: (response: TracesResponse) => {
        this.traces = response.traces;
        this.total = response.total;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading traces:', err);
        this.error = 'Failed to load evaluation traces';
        this.loading = false;
      },
    });
  }

  viewDetails(trace: EvaluationTrace) {
    this.selectedTrace = trace;
    this.showDetails = true;
  }

  closeDetails() {
    this.showDetails = false;
    this.selectedTrace = null;
  }

  deleteTrace(traceId: string) {
    if (!confirm('Are you sure you want to delete this trace?')) {
      return;
    }

    this.adminService.deleteEvaluationTrace(traceId).subscribe({
      next: () => {
        this.loadTraces();
        if (this.selectedTrace?.trace_id === traceId) {
          this.closeDetails();
        }
      },
      error: (err) => {
        console.error('Error deleting trace:', err);
        alert('Failed to delete trace');
      },
    });
  }

  nextPage() {
    if (this.offset + this.limit < this.total) {
      this.offset += this.limit;
      this.loadTraces();
    }
  }

  previousPage() {
    if (this.offset >= this.limit) {
      this.offset -= this.limit;
      this.loadTraces();
    }
  }

  Math = Math;
  Object = Object;

  getScoreColor(score: number): string {
    if (score >= 8) return 'text-emerald-600';
    if (score >= 6) return 'text-yellow-600';
    return 'text-red-600';
  }
}

