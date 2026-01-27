// Service/admin.service.ts
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface DashboardStats {
  kpis: {
    active_users: number;
    new_users_this_month: number;
    new_users_delta: number;
    retention_rate: number;
    avg_session_duration: string;
  };
  user_activity: {
    labels: string[];
    values: number[];
  };
  model_performance: {
    labels: string[];
    series: Array<{
      name: string;
      values: number[];
      color: string;
    }>;
  };
  prompt_statistics: {
    average_prompt_length: number;
    success_rate: number;
    response_time: number;
    error_rate: number;
  };
  system_health: Array<{
    label: string;
    status: 'Operational' | 'Degraded' | 'Down' | 'Warning';
  }>;
  top_users: Array<{
    id: string;
    name: string;
    joined: string;
    lastActive: string;
    prompts: number;
    avgScore: number;
    plan: string;
  }>;
  evaluation_stats: {
    total_evaluations: number;
    recent_evaluations: number;
    average_score: number;
    average_processing_time: number;
  };
}

export interface EvaluationTrace {
  id: string;
  trace_id: string;
  prompt: string;
  timestamp: string;
  overall_score: number;
  base_scores: Record<string, number>;
  final_scores: Record<string, number>;
  suggestions: string[];
  improved_prompt?: string;
  improved_scores?: Record<string, number>;
}

export interface TracesResponse {
  traces: EvaluationTrace[];
  total: number;
  limit: number;
  offset: number;
}

export interface SystemPerformance {
  cpu: {
    percent: number;
    cores: number;
  };
  memory: {
    total_gb: number;
    used_gb: number;
    percent: number;
    available_gb: number;
  };
  disk: {
    total_gb: number;
    used_gb: number;
    percent: number;
    free_gb: number;
  };
  process: {
    memory_mb: number;
    cpu_percent: number;
  };
}

export interface ModelConfiguration {
  status: string;
  embedder?: string;
  targets?: string[];
  version?: string;
  model_path?: string;
  scaler_path?: string;
  message?: string;
}

export interface SystemUsage {
  period_days: number;
  total_evaluations: number;
  daily_usage: Array<{
    date: string;
    count: number;
  }>;
}

export interface MaintenanceInfo {
  platform: string;
  python_version: string;
  uptime: string;
  last_update: string;
  database_size_mb: number;
  log_files: string[];
}

@Injectable({
  providedIn: 'root',
})
export class AdminService {
  constructor(private api: ApiService) {}

  getDashboardStats(): Observable<DashboardStats> {
    return this.api.get<DashboardStats>('/admin/dashboard/stats');
  }

  getEvaluationTraces(
    limit: number = 50,
    offset: number = 0,
    traceId?: string
  ): Observable<TracesResponse> {
    const params: any = { limit, offset };
    if (traceId) {
      params.trace_id = traceId;
    }
    return this.api.get<TracesResponse>('/admin/traces', params);
  }

  deleteEvaluationTrace(traceId: string): Observable<{ message: string }> {
    return this.api.delete<{ message: string }>(`/admin/traces/${traceId}`);
  }

  getSystemPerformance(): Observable<SystemPerformance> {
    return this.api.get<SystemPerformance>('/admin/system/performance');
  }

  getModelConfigurations(): Observable<ModelConfiguration> {
    return this.api.get<ModelConfiguration>('/admin/models/config');
  }

  updateModelConfiguration(config: Partial<ModelConfiguration>): Observable<{ message: string }> {
    return this.api.put<{ message: string }>('/admin/models/config', config);
  }

  getSystemUsage(days: number = 30): Observable<SystemUsage> {
    return this.api.get<SystemUsage>('/admin/system/usage', { days });
  }

  getMaintenanceInfo(): Observable<MaintenanceInfo> {
    return this.api.get<MaintenanceInfo>('/admin/system/maintenance');
  }

  cleanupOldData(daysToKeep: number = 90): Observable<{ message: string; deleted_count: number }> {
    return this.api.post<{ message: string; deleted_count: number }>(
      '/admin/system/maintenance/cleanup',
      { days_to_keep: daysToKeep },
      true
    );
  }
}

