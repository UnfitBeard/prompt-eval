// services/auth.service.ts
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { computed, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { BehaviorSubject, map, Observable, switchMap, tap } from 'rxjs';
import { environment } from '../environments/environment';
import { User, TokenResponse, UserRole } from '../models/course.model';
import { ApiService } from './api.service';

export type LoginFormValue = {
  email: string;
  password: string;
};

export type RegistrationFormValue = {
  fullName: string;
  email: string;
  password: string;
  confirmPassword?: string;
  organization?: string;
  agree?: boolean;
  /** Optional escape hatch if the UI ever captures username explicitly. */
  username?: string;
};

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private currentUserSubject = new BehaviorSubject<User | null>(null);
  public currentUser$ = this.currentUserSubject.asObservable();

  private tokenRefreshTimeout: any;

  // Keep backwards-compatibility with components that expect a Signal-style API.
  private _loggedIn = signal<boolean>(!!localStorage.getItem('access_token'));
  loggedIn = computed(() => this._loggedIn());

  constructor(
    private apiService: ApiService,
    private http: HttpClient,
    private router: Router
  ) {
    this.loadCurrentUser();
  }

  /** For guards/components that previously used `authService.token`. */
  get token(): string | null {
    return this.getToken();
  }

  /** Register using the registration form's shape; we derive `username` automatically. */
  register(form: RegistrationFormValue): Observable<TokenResponse> {
    const username =
      form.username?.trim() ||
      this.deriveUsernameFromEmailOrName(form.email, form.fullName);

    const userData = {
      username,
      email: form.email,
      password: form.password,
      full_name: form.fullName,
      // Note: confirmPassword/organization/agree are UI-only fields.
    };

    // After registering, immediately log in so the dashboard route (guarded) works.
    return this.apiService.post<User>('/auth/register', userData, false).pipe(
      tap((user) => this.currentUserSubject.next(user)),
      switchMap(() => this.login({ email: form.email, password: form.password }))
    );
  }

  /** Login using the login form's shape ({ email, password }). */
  login(form: LoginFormValue): Observable<TokenResponse> {
    // Many backends (e.g. FastAPI OAuth2PasswordRequestForm) require the field name `username`.
    const params = new URLSearchParams();
    params.append('username', form.email);
    params.append('password', form.password);

    return this.http
      .post<any>(`${environment.apiUrl}/api/v1/auth/login`, params.toString(), {
        headers: new HttpHeaders({
          'Content-Type': 'application/x-www-form-urlencoded',
          Accept: 'application/json',
        }),
      })
      .pipe(
        map((response) => (response?.data ?? response) as TokenResponse),
        tap((response) => {
          this.setTokens(response.access_token, response.refresh_token);
          this.currentUserSubject.next(response.user);
          this.scheduleTokenRefresh(response.expires_in);
        })
      );
  }

  logout(): void {
    this.clearToken();
    this.currentUserSubject.next(null);
    this._loggedIn.set(false);

    if (this.tokenRefreshTimeout) {
      clearTimeout(this.tokenRefreshTimeout);
    }

    this.router.navigate(['/login']);
  }

  refreshToken(): Observable<TokenResponse> {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
      this.logout();
      throw new Error('No refresh token available');
    }

    return this.apiService
      .post<TokenResponse>(
        '/auth/refresh',
        {
          refresh_token: refreshToken,
        },
        false
      )
      .pipe(
        tap((response) => {
          this.setTokens(response.access_token, response.refresh_token);
          this.currentUserSubject.next(response.user);
          this.scheduleTokenRefresh(response.expires_in);
        })
      );
  }

  getCurrentUser(): Observable<User> {
    return this.apiService.get<User>('/auth/me');
  }

  updateProfile(updateData: any): Observable<User> {
    return this.apiService
      .put<User>('/users/me', updateData)
      .pipe(tap((user) => this.currentUserSubject.next(user)));
  }

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  clearToken(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  }

  private setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);
    this._loggedIn.set(true);
  }

  private deriveUsernameFromEmailOrName(email: string, fullName: string): string {
    const fromEmail = (email || '').split('@')[0] || '';
    const base = (fromEmail || fullName || 'user').trim().toLowerCase();

    // Keep it URL/DB friendly: alnum + underscores.
    const normalized = base
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+/, '')
      .replace(/_+$/, '');

    return normalized || 'user';
  }

  private scheduleTokenRefresh(expiresIn: number): void {
    // Refresh token 1 minute before expiration
    const refreshTime = (expiresIn - 60) * 1000;

    if (this.tokenRefreshTimeout) {
      clearTimeout(this.tokenRefreshTimeout);
    }

    this.tokenRefreshTimeout = setTimeout(() => {
      this.refreshToken().subscribe({
        error: () => this.logout(),
      });
    }, refreshTime);
  }

  private loadCurrentUser(): void {
    if (this.isAuthenticated()) {
      this.getCurrentUser().subscribe({
        next: (user) => this.currentUserSubject.next(user),
        error: () => {
          // Token might be expired, try to refresh
          this.refreshToken().subscribe({
            error: () => this.logout(),
          });
        },
      });
    }
  }

  // Check if user has required role
  hasRole(requiredRole: UserRole): boolean {
    const user = this.currentUserSubject.value;
    if (!user) return false;

    // Admins have access to everything
    if (user.role === UserRole.ADMIN) return true;

    return user.role === requiredRole;
  }

  // Check if user is instructor
  isInstructor(): boolean {
    return this.hasRole(UserRole.INSTRUCTOR);
  }

  // Check if user is admin
  isAdmin(): boolean {
    return this.hasRole(UserRole.ADMIN);
  }
}
