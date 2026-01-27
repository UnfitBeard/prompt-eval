import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';

export enum NotificationType {
  SUCCESS = 'success',
  ERROR = 'error',
  WARNING = 'warning',
  INFO = 'info'
}

export interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  message: string;
  duration?: number; // milliseconds, 0 = persistent
  timestamp: Date;
}

@Injectable({
  providedIn: 'root'
})
export class NotificationService {
  private notificationsSubject = new BehaviorSubject<Notification[]>([]);
  public notifications$: Observable<Notification[]> = this.notificationsSubject.asObservable();

  constructor() {}

  /**
   * Show a success notification
   */
  success(title: string, message: string, duration: number = 3000): void {
    this.addNotification(NotificationType.SUCCESS, title, message, duration);
  }

  /**
   * Show an error notification
   */
  error(title: string, message: string, duration: number = 5000): void {
    this.addNotification(NotificationType.ERROR, title, message, duration);
  }

  /**
   * Show a warning notification
   */
  warning(title: string, message: string, duration: number = 4000): void {
    this.addNotification(NotificationType.WARNING, title, message, duration);
  }

  /**
   * Show an info notification
   */
  info(title: string, message: string, duration: number = 3000): void {
    this.addNotification(NotificationType.INFO, title, message, duration);
  }

  /**
   * Add a notification to the queue
   */
  private addNotification(
    type: NotificationType,
    title: string,
    message: string,
    duration: number
  ): void {
    const notification: Notification = {
      id: this.generateId(),
      type,
      title,
      message,
      duration,
      timestamp: new Date()
    };

    const current = this.notificationsSubject.value;
    this.notificationsSubject.next([...current, notification]);

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        this.remove(notification.id);
      }, duration);
    }
  }

  /**
   * Remove a notification by ID
   */
  remove(id: string): void {
    const current = this.notificationsSubject.value;
    this.notificationsSubject.next(current.filter(n => n.id !== id));
  }

  /**
   * Clear all notifications
   */
  clearAll(): void {
    this.notificationsSubject.next([]);
  }

  /**
   * Generate a unique ID for notifications
   */
  private generateId(): string {
    return `notif_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Parse HTTP error and return user-friendly message
   */
  parseHttpError(error: any): { title: string; message: string } {
    // Network error / No internet
    if (error.status === 0) {
      return {
        title: 'Connection Error',
        message: 'Unable to connect to the server. Please check your internet connection.'
      };
    }

    // Authentication errors
    if (error.status === 401) {
      return {
        title: 'Authentication Failed',
        message: error.error?.message || 'Invalid credentials. Please try again.'
      };
    }

    // Permission errors
    if (error.status === 403) {
      return {
        title: 'Access Denied',
        message: error.error?.message || 'You do not have permission to perform this action.'
      };
    }

    // Not found
    if (error.status === 404) {
      return {
        title: 'Not Found',
        message: error.error?.message || 'The requested resource was not found.'
      };
    }

    // Rate limiting / API quota
    if (error.status === 429) {
      return {
        title: 'Rate Limit Exceeded',
        message: error.error?.message || 'Too many requests. Please try again later.'
      };
    }

    // Server errors
    if (error.status >= 500) {
      // Check for specific AI service errors
      if (error.error?.message?.toLowerCase().includes('gemini')) {
        return {
          title: 'AI Service Error',
          message: 'Gemini API quota exceeded or service unavailable. Please contact the administrator.'
        };
      }
      if (error.error?.message?.toLowerCase().includes('quota') || 
          error.error?.message?.toLowerCase().includes('token')) {
        return {
          title: 'API Quota Exceeded',
          message: 'AI service quota has been exceeded. Please contact the administrator.'
        };
      }
      return {
        title: 'Server Error',
        message: error.error?.message || 'An unexpected server error occurred. Please try again later.'
      };
    }

    // Client errors
    if (error.status >= 400 && error.status < 500) {
      return {
        title: 'Request Error',
        message: error.error?.message || error.message || 'Invalid request. Please check your input and try again.'
      };
    }

    // Default error
    return {
      title: 'Error',
      message: error.error?.message || error.message || 'An unexpected error occurred. Please try again.'
    };
  }
}
