// Components/admin/admin-maintenance/admin-maintenance.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminService, MaintenanceInfo } from '../../../Service/admin.service';

@Component({
  selector: 'app-admin-maintenance',
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-maintenance.component.html',
  styleUrl: './admin-maintenance.component.css',
})
export class AdminMaintenanceComponent implements OnInit {
  private adminService = inject(AdminService);
  
  loading = true;
  error: string | null = null;
  maintenanceInfo: MaintenanceInfo | null = null;
  daysToKeep = 90;
  cleanupLoading = false;

  ngOnInit() {
    this.loadMaintenanceInfo();
  }

  loadMaintenanceInfo() {
    this.loading = true;
    this.error = null;

    this.adminService.getMaintenanceInfo().subscribe({
      next: (info) => {
        this.maintenanceInfo = info;
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading maintenance info:', err);
        this.error = 'Failed to load maintenance information';
        this.loading = false;
      },
    });
  }

  performCleanup() {
    if (!confirm(`This will delete evaluation traces older than ${this.daysToKeep} days. Continue?`)) {
      return;
    }

    this.cleanupLoading = true;
    this.adminService.cleanupOldData(this.daysToKeep).subscribe({
      next: (result) => {
        alert(`Cleanup completed: ${result.deleted_count} records deleted`);
        this.cleanupLoading = false;
        this.loadMaintenanceInfo();
      },
      error: (err) => {
        console.error('Error performing cleanup:', err);
        alert('Failed to perform cleanup');
        this.cleanupLoading = false;
      },
    });
  }
}

