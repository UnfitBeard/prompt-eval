import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { ModuleProgress } from '../../models/course.model';
import {
  StaticCourseDefinition,
  StaticModuleDefinition,
} from '../../models/dashboard-static-data';

/**
 * ModuleProgressCard
 * -------------------
 * Shows module-level (lesson-level) progress and XP for the selected
 * course.
 *
 * Dynamic data:
 *  - `modules`: ModuleProgress[] from GET /api/v1/user/courses/{id}/modules
 *
 * Static data:
 *  - `staticCourse`: StaticCourseDefinition from the frontend static
 *    definitions. This lets you display planned XP, descriptions,
 *    ordering, etc., even if the backend schema changes.
 */
@Component({
  selector: 'app-module-progress-card',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './module-progress-card.component.html',
})
export class ModuleProgressCardComponent {
  @Input() modules: ModuleProgress[] = [];
  @Input() staticCourse: StaticCourseDefinition | null = null;
  @Input() loading = false;

  getStaticModule(moduleId: string): StaticModuleDefinition | undefined {
    return this.staticCourse?.modules.find((m) => m.id === moduleId);
  }
}
