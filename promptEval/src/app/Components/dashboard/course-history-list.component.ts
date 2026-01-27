import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { CourseProgress } from '../../models/course.model';
import { StaticCourseDefinition } from '../../models/dashboard-static-data';

/**
 * CourseHistoryList
 * ------------------
 * Renders the user's course history as a list.
 *
 * Dynamic data:
 *  - `courses`: array of CourseProgress objects from the backend
 *    (/api/v1/user/progress -> summary.enrolled_courses).
 *
 * Static data:
 *  - `staticDefinitions`: optional static course definitions from
 *    `STATIC_COURSE_DEFINITIONS` used to enrich the UI (e.g. show
 *    estimated hours) without additional backend calls.
 *
 * Modification points:
 *  - Extend the template to show more metadata (difficulty, tags,
 *    categories) as your product evolves.
 */
@Component({
  selector: 'app-course-history-list',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './course-history-list.component.html',
})
export class CourseHistoryListComponent {
  @Input() courses: CourseProgress[] = [];
  @Input() staticDefinitions: StaticCourseDefinition[] = [];
  @Input() selectedCourseId: string | null = null;
  @Input() loading = false;
  @Input() error: string | null = null;

  @Output() courseSelected = new EventEmitter<string>();

  // Helper: derive a human-readable status from dynamic progress
  getStatus(course: CourseProgress): string {
    if (course.progress_percentage >= 100) {
      return 'Completed';
    }
    if (course.completed_lessons > 0) {
      return 'In progress';
    }
    return 'Not started';
  }

  getStaticCourse(courseId: string): StaticCourseDefinition | undefined {
    return this.staticDefinitions.find((c) => c.id === courseId);
  }

  onSelectCourse(courseId: string): void {
    this.courseSelected.emit(courseId);
  }
}
