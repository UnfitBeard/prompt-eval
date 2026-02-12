import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Achievement } from '../../models/course.model';

/**
 * BadgeDisplay
 * ------------
 * Visual representation of earned (and in-progress) badges.
 *
 * Dynamic data:
 *  - `badges`: Achievement[] from GET /api/v1/user/badges
 *    (backed by ProgressService.get_achievements).
 *
 * Modification points:
 *  - Update styling or grouping logic (e.g., show earned badges first
 *    and locked ones after) without touching backend logic.
 */
@Component({
  selector: 'app-badge-display',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './badge-display.component.html',
})
export class BadgeDisplayComponent {
  @Input() badges: Achievement[] = [];
  @Input() loading = false;

  get earnedBadges(): Achievement[] {
    return this.badges.filter((b) => b.earned);
  }

  get lockedBadges(): Achievement[] {
    return this.badges.filter((b) => !b.earned);
  }
}
