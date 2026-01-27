import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { finalize } from 'rxjs/operators';
import {
  Achievement,
  Certificate,
  ModuleProgress,
  UserDashboardProgress,
  UserDashboardStats,
  UserProgressSummary,
} from '../../models/course.model';
import {
  StaticCourseDefinition,
  STATIC_COURSE_DEFINITIONS,
} from '../../models/dashboard-static-data';
import { CourseService } from '../../Service/course.service';
import { CourseHistoryListComponent } from './course-history-list.component';
import { ModuleProgressCardComponent } from './module-progress-card.component';
import { BadgeDisplayComponent } from './badge-display.component';
import { CertificateViewerComponent } from './certificate-viewer.component';
import { InferredStatsPanelComponent } from './inferred-stats-panel.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    CourseHistoryListComponent,
    ModuleProgressCardComponent,
    BadgeDisplayComponent,
    CertificateViewerComponent,
    InferredStatsPanelComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent implements OnInit {
  // Static course definitions that encode the curriculum structure.
  // These are merged with dynamic user data fetched from the backend.
  staticCourses = STATIC_COURSE_DEFINITIONS;

  // ===== Backend-derived state =====
  summary: UserProgressSummary | null = null;
  stats: UserDashboardStats | null = null;

  courseHistoryLoading = false;
  courseHistoryError: string | null = null;

  selectedCourseId: string | null = null;
  modulesByCourse: Record<string, ModuleProgress[]> = {};
  modulesLoading = false;

  badges: Achievement[] = [];
  badgesLoading = false;

  certificates: Certificate[] = [];
  certificatesLoading = false;

  constructor(private courseService: CourseService) {}

  ngOnInit(): void {
    this.loadOverview();
    this.loadBadges();
    this.loadCertificates();
  }

  // ===== Data loading =====

  private loadOverview(): void {
    this.courseHistoryLoading = true;
    this.courseHistoryError = null;

    this.courseService
      .getUserDashboardProgress()
      .pipe(finalize(() => (this.courseHistoryLoading = false)))
      .subscribe({
        next: (res: UserDashboardProgress) => {
          this.summary = res.summary;
          this.recalculateStats();

          // Auto-select the first course (if any) to immediately show
          // module-level details.
          if (this.summary.enrolled_courses?.length && !this.selectedCourseId) {
            this.onCourseSelected(this.summary.enrolled_courses[0].course_id);
          }
        },
        error: (err: Error) => {
          this.courseHistoryError = err.message || 'Failed to load progress';
        },
      });
  }

  private loadBadges(): void {
    this.badgesLoading = true;
    this.courseService
      .getUserBadges()
      .pipe(finalize(() => (this.badgesLoading = false)))
      .subscribe({
        next: (badges) => (this.badges = badges || []),
        error: () => (this.badges = []),
      });
  }

  private loadCertificates(): void {
    this.certificatesLoading = true;
    this.courseService
      .getUserCertificates()
      .pipe(finalize(() => (this.certificatesLoading = false)))
      .subscribe({
        next: (certs) => (this.certificates = certs || []),
        error: () => (this.certificates = []),
      });
  }

  onCourseSelected(courseId: string): void {
    this.selectedCourseId = courseId;

    // If we've already loaded modules for this course, reuse them.
    if (this.modulesByCourse[courseId]) {
      return;
    }

    this.modulesLoading = true;
    this.courseService
      .getUserCourseModules(courseId)
      .pipe(finalize(() => (this.modulesLoading = false)))
      .subscribe({
        next: (modules) => {
          this.modulesByCourse[courseId] = modules || [];
          this.recalculateStats();
        },
        error: () => {
          this.modulesByCourse[courseId] = [];
        },
      });
  }

  get selectedStaticCourse(): StaticCourseDefinition | null {
    if (!this.selectedCourseId) {
      return null;
    }

    return (
      this.staticCourses.find(
        (course) => course.id === this.selectedCourseId
      ) ?? null
    );
  }

  // ===== Inference logic (client-side statistics) =====

  private recalculateStats(): void {
    if (!this.summary) {
      this.stats = null;
      return;
    }

    const totalCourses = this.summary.total_courses || 0;
    const completedCourses = this.summary.completed_courses || 0;
    const completionRate =
      totalCourses > 0 ? (completedCourses / totalCourses) * 100 : 0;

    const enrolled = this.summary.enrolled_courses || [];
    const totalLessonsCompleted = enrolled.reduce(
      (acc, c) => acc + c.completed_lessons,
      0
    );
    const totalLessons = enrolled.reduce(
      (acc, c) => acc + c.total_lessons,
      0
    );

    const averageCourseProgress =
      totalCourses > 0
        ? enrolled.reduce((acc, c) => acc + c.progress_percentage, 0) /
          totalCourses
        : 0;

    const xpProgressToNextLevel = this.computeXpProgressToNextLevel(
      this.summary.total_xp
    );

    this.stats = {
      completionRate,
      averageCourseProgress,
      totalLessonsCompleted,
      totalLessons,
      xpProgressToNextLevel,
    };
  }

  /**
   * Simple XP curve that maps raw XP to a 0–100% progress value towards
   * the next level. The actual level thresholds are easy to tweak
   * without touching backend code.
   */
  private computeXpProgressToNextLevel(totalXp: number): number {
    // Example thresholds (cumulative XP):
    // 0, 500, 1500, 3000, 5000, 8000...
    const thresholds = [0, 500, 1500, 3000, 5000, 8000];

    let currentIndex = 0;
    for (let i = 0; i < thresholds.length; i++) {
      if (totalXp >= thresholds[i]) {
        currentIndex = i;
      } else {
        break;
      }
    }

    const current = thresholds[currentIndex] ?? 0;
    const next = thresholds[currentIndex + 1] ?? current + 1; // avoid div-by-zero

    if (totalXp >= next) {
      return 100;
    }

    const span = next - current;
    const progressed = totalXp - current;
    return Math.max(0, Math.min(100, (progressed / span) * 100));
  }
}
