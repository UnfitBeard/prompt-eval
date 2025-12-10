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
  attempt: [];
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
  scores: {
    final_scores: {
      clarity: number | null;
      context: number | null;
      creativity: number | null;
      relevance: number | null;
      specificity: number | null;
    };
    base_scores: {
      clarity: number | null;
      context: number | null;
      creativity: number | null;
      relevance: number | null;
      specificity: number | null;
    };
  };
  top_rag_prompts: any;
  llm_evaluation: {
    clarity: number | null;
    context: number | null;
    creativity: number | null;
    relevance: number | null;
    specificity: number | null;
    suggestions: Suggestion[];
    rewriteVersions: RewriteVersion[];
  };
  trace_id: any;
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
  private baseUrl = 'http://localhost:8000';

  evaluatePrompt(prompt: string): Observable<EvaluateResponse> {
    return this.http
      .post<EvaluateResponse>(`${this.baseUrl}/evaluate`, { prompt })
      .pipe(catchError(this.handle));
  }

  getPromptScores(prompt: string): Observable<ScoresResponse> {
    return this.http
      .post<ScoresResponse>(`${this.baseUrl}/process_prompt`, { prompt })
      .pipe(catchError(this.handle));
  }

  private handle(err: HttpErrorResponse) {
    const msg =
      err.error?.error || err.message || 'Request failed. Please try again.';
    return throwError(() => new Error(msg));
  }
}
