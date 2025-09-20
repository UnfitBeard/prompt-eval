import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';

export interface Suggestion {
  text: string;
}
export interface Improvement {
  text: string;
}
export interface RewriteVersion {
  title: string;
  content: string;
  improvements: Improvement[];
}

/** Response shape from your /api/evaluate endpoint */
export interface EvaluateResponse {
  clarity: number | null;
  context: number | null;
  relevance: number | null;
  specificity: number | null;
  creativity: number | null;
  suggestions?: Suggestion[];
  rewriteVersions?: RewriteVersion[];
  _raw?: string; // present when parse fails
  _error?: string; // parse error message if any
}

export interface ScoresResponse {
  Clarity: number | null;
  Context: number | null;
  Creativity: number | null;
  Relevance: number | null;
  Specificity: number | null;
}

/** Response shape from /api/recommendations */
export interface RecommendationsResponse {
  rewriteVersions: RewriteVersion[];
  notes?: { text: string }[];
  _raw?: string;
  _error?: string;
}

@Injectable({
  providedIn: 'root',
})
export class PromptEvalService {
  private http = inject(HttpClient);
  private baseUrl = 'http://localhost:10000/api/v1/prompts';

  evaluatePrompt(prompt: string): Observable<EvaluateResponse> {
    return this.http
      .post<EvaluateResponse>(`${this.baseUrl}/evaluate`, { prompt })
      .pipe(catchError(this.handle));
  }

  getPromptScores(prompt: string): Observable<ScoresResponse> {
    return this.http
      .post<ScoresResponse>(`${this.baseUrl}/get-results`, { prompt })
      .pipe(catchError(this.handle));
  }

  private handle(err: HttpErrorResponse) {
    const msg =
      err.error?.error || err.message || 'Request failed. Please try again.';
    return throwError(() => new Error(msg));
  }
}
