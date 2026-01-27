import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export interface StartedCourse {
  courseId: string;
  startedAt: Date;
  progress: number;
}

@Injectable({
  providedIn: 'root'
})
export class StartedCoursesService {
  private readonly STORAGE_KEY = 'startedCourses';
  private startedCoursesSubject = new BehaviorSubject<Map<string, StartedCourse>>(new Map());
  
  public startedCourses$: Observable<Map<string, StartedCourse>> = this.startedCoursesSubject.asObservable();

  constructor() {
    this.loadFromStorage();
  }

  /**
   * Load started courses from localStorage
   */
  private loadFromStorage(): void {
    try {
      const saved = localStorage.getItem(this.STORAGE_KEY);
      if (saved) {
        const data = JSON.parse(saved);
        const coursesMap = new Map<string, StartedCourse>();
        
        Object.entries(data).forEach(([courseId, value]: [string, any]) => {
          coursesMap.set(courseId, {
            courseId,
            startedAt: new Date(value.startedAt),
            progress: value.progress || 0
          });
        });
        
        this.startedCoursesSubject.next(coursesMap);
      }
    } catch (error) {
      console.error('Failed to load started courses:', error);
    }
  }

  /**
   * Save started courses to localStorage
   */
  private saveToStorage(): void {
    try {
      const data: any = {};
      const courses = this.startedCoursesSubject.value;
      
      courses.forEach((course, courseId) => {
        data[courseId] = {
          startedAt: course.startedAt.toISOString(),
          progress: course.progress
        };
      });
      
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(data));
    } catch (error) {
      console.error('Failed to save started courses:', error);
    }
  }

  /**
   * Check if a course has been started
   */
  isCourseStarted(courseId: string): boolean {
    return this.startedCoursesSubject.value.has(courseId);
  }

  /**
   * Get progress for a specific course
   */
  getCourseProgress(courseId: string): number {
    return this.startedCoursesSubject.value.get(courseId)?.progress || 0;
  }

  /**
   * Start a course
   */
  startCourse(courseId: string): void {
    const courses = this.startedCoursesSubject.value;
    
    if (!courses.has(courseId)) {
      courses.set(courseId, {
        courseId,
        startedAt: new Date(),
        progress: 0
      });
      
      this.startedCoursesSubject.next(new Map(courses));
      this.saveToStorage();
    }
  }

  /**
   * Update course progress
   */
  updateCourseProgress(courseId: string, progress: number): void {
    const courses = this.startedCoursesSubject.value;
    const course = courses.get(courseId);
    
    if (course) {
      course.progress = Math.round(Math.max(0, Math.min(100, progress)));
      this.startedCoursesSubject.next(new Map(courses));
      this.saveToStorage();
    }
  }

  /**
   * Get all started courses
   */
  getAllStartedCourses(): StartedCourse[] {
    return Array.from(this.startedCoursesSubject.value.values());
  }

  /**
   * Get started courses as a map
   */
  getStartedCoursesMap(): Map<string, StartedCourse> {
    return new Map(this.startedCoursesSubject.value);
  }
}
