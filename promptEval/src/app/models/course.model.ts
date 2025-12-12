// models/course.model.ts
export enum CourseDifficulty {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
}

export enum CourseStatus {
  DRAFT = 'draft',
  PUBLISHED = 'published',
  ARCHIVED = 'archived',
}

export enum UserLevel {
  BEGINNER = 'beginner',
  INTERMEDIATE = 'intermediate',
  ADVANCED = 'advanced',
  EXPERT = 'expert',
}

export enum UserRole {
  STUDENT = 'student',
  INSTRUCTOR = 'instructor',
  ADMIN = 'admin',
}

export interface Course {
  id: string;
  title: string;
  slug: string;
  description: string;
  short_description: string;
  difficulty: CourseDifficulty;
  tags: string[];
  estimated_hours: number;
  thumbnail_url?: string;
  prerequisites: string[];
  instructor_id: string;
  instructor_name: string;
  status: CourseStatus;
  total_lessons: number;
  total_xp: number;
  enrolled_count: number;
  avg_rating?: number;
  review_count: number;
  created_at: string;
  progress_percentage?: number;
}

export interface CourseListResponse {
  courses: Course[];
  total: number;
  limit: number;
  skip: number;
}

// User models
export interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  role: UserRole;
  level: UserLevel;
  xp: number;
  streak_days: number;
  created_at: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Lesson models
export enum LessonType {
  THEORY = 'theory',
  PRACTICE = 'practice',
  PROJECT = 'project',
  QUIZ = 'quiz',
}

export enum QuestionType {
  MULTIPLE_CHOICE = 'multiple_choice',
  SINGLE_CHOICE = 'single_choice',
  CODE = 'code',
  TEXT = 'text',
  TRUE_FALSE = 'true_false',
}

export interface QuestionOption {
  id: string;
  text: string;
  is_correct: boolean;
  explanation?: string;
}

export interface LessonQuestion {
  id: string;
  type: QuestionType;
  question: string;
  description?: string;
  options?: QuestionOption[];
  correct_answer?: string | string[];
  hint?: string;
  explanation?: string;
  xp_reward: number;
  code_template?: string;
  test_cases?: any[];
  difficulty: string;
}

export interface LessonContent {
  type: LessonType;
  content: any;
}

export interface Lesson {
  id: string;
  title: string;
  slug: string;
  description: string;
  course_id: string;
  order: number;
  content: LessonContent;
  questions: LessonQuestion[];
  estimated_minutes: number;
  prerequisites: string[];
  tags: string[];
  total_xp: number;
  completed_count: number;
  is_completed?: boolean;
  user_xp_earned?: number;
  next_lesson_id?: string;
  prev_lesson_id?: string;
  created_at: string;
}

export interface LessonAttemptRequest {
  answers: { [questionId: string]: any };
  time_spent_seconds: number;
}

export interface LessonAttemptResponse {
  attempt_id: string;
  correct_answers: number;
  total_questions: number;
  score_percentage: number;
  xp_earned: number;
  status: string;
  feedback: string[];
  next_lesson_id?: string;
}

// Progress models
export interface CourseProgress {
  course_id: string;
  course_title: string;
  completed_lessons: number;
  total_lessons: number;
  progress_percentage: number;
  total_xp_earned: number;
  current_lesson_id?: string;
  started_at: string;
  last_accessed: string;
}

export interface UserProgressSummary {
  user_id: string;
  total_courses: number;
  completed_courses: number;
  total_xp: number;
  level: string;
  streak_days: number;
  enrolled_courses: CourseProgress[];
}

export interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: string;
  xp_reward: number;
  earned_at?: string;
  progress?: number;
}

// API Response models
export interface APIResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
