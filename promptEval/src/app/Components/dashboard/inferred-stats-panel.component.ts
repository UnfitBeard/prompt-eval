import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { UserDashboardStats, UserProgressSummary } from '../../models/course.model';

/**
 * InferredStatsPanel
 * -------------------
 * Presents derived statistics such as completion rate, average course
 * progress, and XP progress to the next level.
 *
 * All calculations are performed on the client side in the main
 * DashboardComponent; this component is purely presentational.
 */
@Component({
  selector: 'app-inferred-stats-panel',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './inferred-stats-panel.component.html',
})
export class InferredStatsPanelComponent {
  @Input() summary: UserProgressSummary | null = null;
  @Input() stats: UserDashboardStats | null = null;
  @Input() loading = false;
}
