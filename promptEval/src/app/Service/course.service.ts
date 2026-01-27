// services/course.service.ts
import { Injectable } from '@angular/core';
import { Observable, map, tap } from 'rxjs';
import { ApiService } from './api.service';
import {
  Course,
  CourseListResponse,
  Lesson,
  LessonAttemptRequest,
  LessonAttemptResponse,
  CourseProgress,
  UserProgressSummary,
  Achievement,
  ModuleProgress,
  Certificate,
  UserDashboardProgress,
} from '../models/course.model';

@Injectable({
  providedIn: 'root',
})
export class CourseService {
  constructor(private apiService: ApiService) {}

  // Course methods
  getCourses(params?: {
    difficulty?: string;
    limit?: number;
    skip?: number;
  }): Observable<CourseListResponse> {
    return this.apiService.get<CourseListResponse>('/courses', params).pipe(
      tap((res) => {
        console.log('[CourseService] /courses response:', res);
      })
    );
  }

  getCourseById(courseId: string): Observable<Course> {
    return this.apiService.get<Course>(`/courses/${courseId}`);
  }

  enrollInCourse(courseId: string): Observable<any> {
    return this.apiService.post(`/courses/${courseId}/enroll`, {});
  }

  getCourseProgress(courseId: string): Observable<CourseProgress> {
    return this.apiService.get<CourseProgress>(`/courses/${courseId}/progress`);
  }

  // Lesson methods
  getLessonById(lessonId: string): Observable<Lesson> {
    return this.apiService.get<Lesson>(`/lessons/${lessonId}`);
  }

  submitLessonAttempt(
    lessonId: string,
    attempt: LessonAttemptRequest
  ): Observable<LessonAttemptResponse> {
    return this.apiService.post<LessonAttemptResponse>(
      `/lessons/${lessonId}/attempt`,
      attempt
    );
  }

  getLessonAttempts(lessonId: string, limit: number = 10): Observable<any[]> {
    return this.apiService.get<any[]>(`/lessons/${lessonId}/attempts`, {
      limit,
    });
  }

  markLessonAsCompleted(lessonId: string): Observable<any> {
    return this.apiService.post(`/lessons/${lessonId}/complete`, {});
  }

  // Progress methods
  getUserProgressSummary(): Observable<UserProgressSummary> {
    return this.apiService.get<UserProgressSummary>('/progress/summary');
  }

  getRecentActivity(limit: number = 20): Observable<any[]> {
    return this.apiService.get<any[]>('/progress/activity', { limit });
  }

  getStreakData(days: number = 30): Observable<any> {
    return this.apiService.get<any>('/progress/streak', { days });
  }

  getAchievements(): Observable<Achievement[]> {
    return this.apiService.get<Achievement[]>('/progress/achievements');
  }

  /**
   * Dashboard-specific endpoints
   */
  getUserDashboardProgress(): Observable<UserDashboardProgress> {
    // GET /api/v1/user/progress
    return this.apiService.get<UserDashboardProgress>('/user/progress');
  }

  getUserCourseModules(courseId: string): Observable<ModuleProgress[]> {
    // GET /api/v1/user/courses/{courseId}/modules
    return this.apiService.get<ModuleProgress[]>(
      `/user/courses/${courseId}/modules`
    );
  }

  getUserBadges(): Observable<Achievement[]> {
    // GET /api/v1/user/badges
    return this.apiService.get<Achievement[]>('/user/badges');
  }

  getUserCertificates(): Observable<Certificate[]> {
    // GET /api/v1/user/certificates
    return this.apiService.get<Certificate[]>('/user/certificates');
  }

  getLeaderboard(limit: number = 50): Observable<any[]> {
    return this.apiService.get<any[]>('/progress/leaderboard', { limit });
  }

  // Academy course catalog (Prompt Engineering Academy)
  getAcademyCourses(): Observable<any[]> {
    return this.apiService.get<any[]>('/courses/academy').pipe(
      tap((courses) => {
        console.log('[CourseService] /courses/academy response:', courses);
      })
    );
  }

  /**
   * Award XP on the backend for frontend-only modules.
   *
   * This keeps the dashboard's total XP in sync with the
   * in-course "XP mode" even for static modules that are not
   * yet backed by real Lesson documents in Mongo.
   */
  addXp(amount: number, reason?: string): Observable<{ total_xp: number }> {
    return this.apiService.post<{ total_xp: number }>('/progress/xp', {
      amount,
      reason,
    });
  }

  // Helper methods
  getNextLesson(
    courseId: string,
    currentLessonId: string
  ): Observable<Lesson | null> {
    return this.apiService.get<Lesson>(
      `/courses/${courseId}/next-lesson/${currentLessonId}`
    );
  }

  getCourseWithProgress(
    courseId: string
  ): Observable<{ course: Course; progress: CourseProgress }> {
    return this.apiService.get<Course>(`/courses/${courseId}`).pipe(
      map((course) => ({
        course,
        progress: {} as CourseProgress, // Will be fetched separately
      }))
    );
  }

  searchCourses(query: string): Observable<Course[]> {
    return this.apiService.get<Course[]>('/courses/search', { q: query });
  }

  getRecommendedCourses(): Observable<Course[]> {
    return this.apiService.get<Course[]>('/courses/recommended');
  }
}
