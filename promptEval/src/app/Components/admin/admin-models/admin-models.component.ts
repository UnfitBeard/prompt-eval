// Components/admin/admin-models/admin-models.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { AdminService, ModelConfiguration } from '../../../Service/admin.service';

@Component({
  selector: 'app-admin-models',
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-models.component.html',
  styleUrl: './admin-models.component.css',
})
export class AdminModelsComponent implements OnInit {
  private adminService = inject(AdminService);
  
  loading = true;
  error: string | null = null;
  config: ModelConfiguration | null = null;
  
  // Form state
  editing = false;
  formData: Partial<ModelConfiguration> = {};

  ngOnInit() {
    this.loadConfiguration();
  }

  loadConfiguration() {
    this.loading = true;
    this.error = null;

    this.adminService.getModelConfigurations().subscribe({
      next: (config) => {
        this.config = config;
        this.formData = { ...config };
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading model configuration:', err);
        this.error = 'Failed to load model configuration';
        this.loading = false;
      },
    });
  }

  startEdit() {
    this.editing = true;
    this.formData = { ...this.config };
  }

  cancelEdit() {
    this.editing = false;
    this.formData = { ...this.config };
  }

  saveConfiguration() {
    if (!this.formData) return;

    this.loading = true;
    this.adminService.updateModelConfiguration(this.formData).subscribe({
      next: () => {
        this.editing = false;
        this.loadConfiguration();
      },
      error: (err) => {
        console.error('Error updating configuration:', err);
        this.error = 'Failed to update model configuration';
        this.loading = false;
      },
    });
  }

  getStatusColor(status: string): string {
    switch (status) {
      case 'configured':
        return 'text-emerald-600';
      case 'not_configured':
        return 'text-orange-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  }
}

