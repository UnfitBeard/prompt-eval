// courses/course-list/course-list.component.ts
import { Component, OnInit, OnDestroy, NgModule } from '@angular/core';
import { Router } from '@angular/router';
import {
  Subscription,
  debounceTime,
  distinctUntilChanged,
  Subject,
} from 'rxjs';
import { CourseService } from '../../../Service/course.service';
import { AuthService } from '../../../Service/auth.service';
import { Course, CourseDifficulty, User } from '../../../models/course.model';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-course-list',
  imports: [ReactiveFormsModule, FormsModule, CommonModule],
  templateUrl: './course-list.component.html',
  styleUrls: ['./course-list.component.css'],
})
export class CourseListComponent implements OnInit, OnDestroy {
  courses: Course[] = [];
  filteredCourses: Course[] = [];
  loading = true;
  error: string | null = null;
  currentUser: User | null = null;

  // Filters
  selectedDifficulty: string = 'all';
  searchQuery: string = '';
  searchQueryChanged = new Subject<string>();

  // Pagination
  totalCourses = 0;
  currentPage = 1;
  pageSize = 12;
  totalPages = 0;

  // Difficulty options
  difficultyOptions = [
    { value: 'all', label: 'All Levels' },
    { value: CourseDifficulty.BEGINNER, label: 'Beginner' },
    { value: CourseDifficulty.INTERMEDIATE, label: 'Intermediate' },
    { value: CourseDifficulty.ADVANCED, label: 'Advanced' },
  ];

  private subscriptions: Subscription[] = [];

  constructor(
    private courseService: CourseService,
    private authService: AuthService,
    private router: Router
  ) {
    // Setup search debouncing
    this.searchQueryChanged
      .pipe(debounceTime(300), distinctUntilChanged())
      .subscribe((query) => {
        this.searchQuery = query;
        this.filterCourses();
      });
  }

  ngOnInit(): void {
    this.loadCourses();

    // Subscribe to user changes
    // const userSub = this.authService.currentUser$.subscribe((user) => {
    //   this.currentUser = user;
    //   if (user) {
    this.loadCourses();
    // }
    // });

    // this.subscriptions.push(userSub);
  }

  loadCourses(): void {
    this.loading = true;
    this.error = null;

    const params: any = {
      limit: this.pageSize,
      skip: (this.currentPage - 1) * this.pageSize,
    };

    if (this.selectedDifficulty !== 'all') {
      params.difficulty = this.selectedDifficulty;
    }

    const coursesSub = this.courseService.getCourses(params).subscribe({
      next: (response) => {
        this.courses = response.courses;
        this.filteredCourses = [...this.courses];
        this.totalCourses = response.total;
        this.totalPages = Math.ceil(this.totalCourses / this.pageSize);
        this.loading = false;
      },
      error: (err) => {
        this.error = err.message || 'Failed to load courses';
        this.loading = false;
      },
    });

    this.subscriptions.push(coursesSub);
  }

  filterCourses(): void {
    if (!this.searchQuery.trim()) {
      this.filteredCourses = [...this.courses];
      return;
    }

    const query = this.searchQuery.toLowerCase().trim();
    this.filteredCourses = this.courses.filter(
      (course) =>
        course.title.toLowerCase().includes(query) ||
        course.description.toLowerCase().includes(query) ||
        course.tags.some((tag) => tag.toLowerCase().includes(query))
    );
  }

  onSearchChange(query: string): void {
    this.searchQueryChanged.next(query);
  }

  onDifficultyChange(difficulty: string): void {
    this.selectedDifficulty = difficulty;
    this.currentPage = 1;
    this.loadCourses();
  }

  onPageChange(page: number): void {
    this.currentPage = page;
    this.loadCourses();
    window.scrollTo(0, 0);
  }

  getDifficultyBadgeClass(difficulty: CourseDifficulty): string {
    switch (difficulty) {
      case CourseDifficulty.BEGINNER:
        return 'badge-beginner';
      case CourseDifficulty.INTERMEDIATE:
        return 'badge-intermediate';
      case CourseDifficulty.ADVANCED:
        return 'badge-advanced';
      default:
        return 'badge-default';
    }
  }

  getDifficultyLabel(difficulty: CourseDifficulty): string {
    return difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
  }

  formatTime(hours: number): string {
    if (hours === 1) return '1 hour';
    return `${hours} hours`;
  }

  getProgressWidth(course: Course): string {
    return course.progress_percentage ? `${course.progress_percentage}%` : '0%';
  }

  viewCourse(courseId: string): void {
    this.router.navigate(['/courses', courseId]);
  }

  enrollCourse(courseId: string, event: Event): void {
    event.stopPropagation();

    if (!this.currentUser) {
      this.router.navigate(['/login'], {
        queryParams: { returnUrl: `/courses/${courseId}` },
      });
      return;
    }

    this.courseService.enrollInCourse(courseId).subscribe({
      next: () => {
        // Refresh the course to show enrolled status
        this.loadCourses();
      },
      error: (err) => {
        console.error('Failed to enroll:', err);
        // Show error message
      },
    });
  }

  isEnrolled(course: Course): boolean {
    return (
      course.progress_percentage !== undefined && course.progress_percentage > 0
    );
  }

  trackByCourseId(index: number, course: Course): string {
    return course.id;
  }

  ngOnDestroy(): void {
    this.subscriptions.forEach((sub) => sub.unsubscribe());
  }
}
