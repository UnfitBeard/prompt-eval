import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output, OnInit } from '@angular/core';
import { CourseProgress } from '../../models/course.model';
import { StaticCourseDefinition } from '../../models/dashboard-static-data';
import { StartedCoursesService, StartedCourse } from '../../Services/started-courses.service';

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
export class CourseHistoryListComponent implements OnInit {
  @Input() courses: CourseProgress[] = [];
  @Input() staticDefinitions: StaticCourseDefinition[] = [];
  @Input() selectedCourseId: string | null = null;
  @Input() loading = false;
  @Input() error: string | null = null;

  @Output() courseSelected = new EventEmitter<string>();

  startedCourses: StartedCourse[] = [];

  constructor(private startedCoursesService: StartedCoursesService) {}

  ngOnInit(): void {
    // Subscribe to started courses from shared service
    this.startedCoursesService.startedCourses$.subscribe(coursesMap => {
      this.startedCourses = Array.from(coursesMap.values());
    });
  }

  // Check if a course is started
  isCourseStarted(courseId: string): boolean {
    return this.startedCoursesService.isCourseStarted(courseId);
  }

  // Get progress for a started course
  getStartedCourseProgress(courseId: string): number {
    return this.startedCoursesService.getCourseProgress(courseId);
  }

  // Helper: derive a human-readable status from dynamic progress
  getStatus(course: CourseProgress): string {
    // Check if manually started via the course list
    if (this.isCourseStarted(course.course_id)) {
      const progress = this.getStartedCourseProgress(course.course_id);
      if (progress >= 100) {
        return 'Completed';
      }
      if (progress > 0) {
        return 'In progress';
      }
      return 'Started';
    }
    
    // Fallback to backend progress
    if (course.progress_percentage >= 100) {
      return 'Completed';
    }
    if (course.completed_lessons > 0) {
      return 'In progress';
    }
    return 'Not started';
  }

  // Get effective progress (prioritize local started courses)
  getEffectiveProgress(course: CourseProgress): number {
    if (this.isCourseStarted(course.course_id)) {
      return this.getStartedCourseProgress(course.course_id);
    }
    return course.progress_percentage || 0;
  }

  getStaticCourse(courseId: string): StaticCourseDefinition | undefined {
    return this.staticDefinitions.find((c) => c.id === courseId);
  }

  onSelectCourse(courseId: string): void {
    this.courseSelected.emit(courseId);
  }
}
