// services/course.service.ts
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
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
    return this.apiService.get<CourseListResponse>('/courses', params);
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

  getLeaderboard(limit: number = 50): Observable<any[]> {
    return this.apiService.get<any[]>('/progress/leaderboard', { limit });
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
