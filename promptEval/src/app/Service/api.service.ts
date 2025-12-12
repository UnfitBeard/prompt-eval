// services/api.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { environment } from '../environments/environment';
import { APIResponse } from '../models/course.model';

@Injectable({
  providedIn: 'root',
})
export class ApiService {
  private apiUrl = environment.apiUrl;
  private apiPrefix = '/api/v1';

  constructor(private http: HttpClient) {}

  private buildUrl(endpoint: string): string {
    // Normalize endpoint to always start with '/'
    const ep = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

    // If the caller already included the prefix, don't double-prefix.
    if (ep === this.apiPrefix || ep.startsWith(`${this.apiPrefix}/`)) {
      return `${this.apiUrl}${ep}`;
    }

    return `${this.apiUrl}${this.apiPrefix}${ep}`;
  }

  private getHeaders(includeAuth: boolean = true): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
      Accept: 'application/json',
    });

    if (includeAuth) {
      const token = localStorage.getItem('access_token');
      if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }
    }

    return headers;
  }

  get<T>(
    endpoint: string,
    params?: any,
    includeAuth: boolean = true
  ): Observable<T> {
    const options = {
      headers: this.getHeaders(includeAuth),
      params: this.createParams(params),
    };

    return this.http.get<any>(this.buildUrl(endpoint), options).pipe(
      map((response) => response.data!),
      catchError(this.handleError)
    );
  }

  post<T>(
    endpoint: string,
    data: any,
    includeAuth: boolean = true
  ): Observable<T> {
    const options = {
      headers: this.getHeaders(includeAuth),
    };

    return this.http.post<any>(this.buildUrl(endpoint), data, options).pipe(
      map((response) => response.data!),
      catchError(this.handleError)
    );
  }

  put<T>(
    endpoint: string,
    data: any,
    includeAuth: boolean = true
  ): Observable<T> {
    const options = {
      headers: this.getHeaders(includeAuth),
    };

    return this.http.put<any>(this.buildUrl(endpoint), data, options).pipe(
      map((response) => response.data!),
      catchError(this.handleError)
    );
  }

  delete<T>(endpoint: string, includeAuth: boolean = true): Observable<T> {
    const options = {
      headers: this.getHeaders(includeAuth),
    };

    return this.http.delete<any>(this.buildUrl(endpoint), options).pipe(
      map((response) => response.data!),
      catchError(this.handleError)
    );
  }

  private createParams(params: any): HttpParams {
    let httpParams = new HttpParams();
    if (params) {
      Object.keys(params).forEach((key) => {
        if (params[key] !== null && params[key] !== undefined) {
          httpParams = httpParams.set(key, params[key].toString());
        }
      });
    }
    return httpParams;
  }

  private handleError(error: any): Observable<never> {
    let errorMessage = 'An unknown error occurred';

    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = error.error.message;
    } else {
      // Server-side error
      if (error.status === 401) {
        // Unauthorized - clear token and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
      }
      errorMessage = error.error?.detail || error.error?.error || error.message;
    }

    console.error('API Error:', error);
    return throwError(() => new Error(errorMessage));
  }
}
