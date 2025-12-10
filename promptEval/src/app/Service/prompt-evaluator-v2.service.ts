// services/prompt-evaluator.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, throwError } from 'rxjs';
import { catchError, tap, map, shareReplay } from 'rxjs/operators';
import { environment } from '../environments/environment';
import {
  PromptEvaluationRequest,
  PromptEvaluationResult,
  EvaluationHistory,
  PromptScores,
} from '../models/prompt.model';

@Injectable({
  providedIn: 'root',
})
export class PromptEvaluatorV2Service {
  private apiUrl = environment.apiUrl;

  // State management
  private loadingSubject = new BehaviorSubject<boolean>(false);
  private evaluationHistorySubject = new BehaviorSubject<EvaluationHistory[]>(
    []
  );
  private lastEvaluationSubject =
    new BehaviorSubject<PromptEvaluationResult | null>(null);

  // Public observables
  loading$ = this.loadingSubject.asObservable();
  evaluationHistory$ = this.evaluationHistorySubject.asObservable();
  lastEvaluation$ = this.lastEvaluationSubject.asObservable();

  constructor(private http: HttpClient) {
    this.loadEvaluationHistory();
  }

  /**
   * Evaluate a single prompt
   */
  evaluatePrompt(
    prompt: string,
    k: number = 3,
    improveIfLow: boolean = true
  ): Observable<PromptEvaluationResult> {
    this.loadingSubject.next(true);

    const request: PromptEvaluationRequest = {
      prompt: prompt.trim(),
      k: k,
      improve_if_low: improveIfLow,
    };

    return this.http
      .post<PromptEvaluationResult>(`${this.apiUrl}/evaluate`, request)
      .pipe(
        tap((result) => {
          console.log(result);
          this.lastEvaluationSubject.next(result);
          this.addToHistory(result);
          this.loadingSubject.next(false);
        }),
        catchError((error) => {
          this.loadingSubject.next(false);
          console.error('Evaluation failed:', error);
          return throwError(
            () => new Error('Failed to evaluate prompt. Please try again.')
          );
        }),
        shareReplay(1)
      );
  }

  /**
   * Evaluate multiple prompts in batch
   */
  batchEvaluate(prompts: string[]): Observable<any> {
    this.loadingSubject.next(true);

    return this.http.post(`${this.apiUrl}/batch_evaluate`, { prompts }).pipe(
      tap(() => this.loadingSubject.next(false)),
      catchError((error) => {
        this.loadingSubject.next(false);
        return throwError(() => new Error('Batch evaluation failed'));
      })
    );
  }

  /**
   * Get evaluation history
   */
  getEvaluationHistory(limit: number = 20): Observable<EvaluationHistory[]> {
    return this.http
      .get<EvaluationHistory[]>(`${this.apiUrl}/history?limit=${limit}`)
      .pipe(
        tap((history) => this.evaluationHistorySubject.next(history)),
        catchError((error) => {
          console.error('Failed to load history:', error);
          return throwError(() => new Error('Failed to load history'));
        })
      );
  }

  /**
   * Get a specific trace for debugging
   */
  getTrace(traceId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/trace/${traceId}`);
  }

  /**
   * Get analysis of why iterations happened
   */
  getIterationAnalysis(traceId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/why_iterate/${traceId}`);
  }

  /**
   * Check API health
   */
  checkHealth(): Observable<any> {
    return this.http
      .get(`${this.apiUrl}/health`)
      .pipe(
        catchError(() => throwError(() => new Error('API is unavailable')))
      );
  }

  /**
   * Generate a visual score summary
   */
  getScoreSummary(scores: PromptScores): {
    labels: string[];
    baseValues: number[];
    finalValues: number[];
    maxScore: number;
    averageScore: number;
  } {
    const dimensions = [
      'clarity',
      'context',
      'relevance',
      'specificity',
      'creativity',
    ];
    const baseValues = dimensions.map(
      (d) => scores.base_scores[d as keyof typeof scores.base_scores]
    );
    const finalValues = dimensions.map(
      (d) => scores.final_scores[d as keyof typeof scores.final_scores]
    );

    const allValues = [...baseValues, ...finalValues];
    const maxScore = Math.max(...allValues);
    const averageScore =
      finalValues.reduce((a, b) => a + b, 0) / finalValues.length;

    return {
      labels: dimensions.map((d) => this.capitalizeFirst(d)),
      baseValues,
      finalValues,
      maxScore,
      averageScore,
    };
  }

  /**
   * Get suggestions grouped by dimension
   */
  getGroupedSuggestions(
    scores: PromptScores,
    suggestions: string[]
  ): { dimension: string; score: number; suggestions: string[] }[] {
    const dimensions = [
      'clarity',
      'context',
      'relevance',
      'specificity',
      'creativity',
    ];

    return dimensions.map((dimension) => {
      const score =
        scores.final_scores[dimension as keyof typeof scores.final_scores];
      const dimensionKeywords = this.getDimensionKeywords(dimension);

      const relevantSuggestions = suggestions.filter((suggestion) =>
        dimensionKeywords.some((keyword) =>
          suggestion.toLowerCase().includes(keyword.toLowerCase())
        )
      );

      return {
        dimension: this.capitalizeFirst(dimension),
        score,
        suggestions:
          relevantSuggestions.length > 0
            ? relevantSuggestions
            : [
                `Consider improving ${dimension} by adding more specific details`,
              ],
      };
    });
  }

  /**
   * Save evaluation to local storage
   */
  private addToHistory(result: PromptEvaluationResult): void {
    try {
      const historyItem: EvaluationHistory = {
        id: crypto.randomUUID(),
        prompt: result.prompt,
        timestamp: new Date().toISOString(),
        base_scores: result.scores.base_scores,
        final_scores: result.scores.final_scores,
        overall_score: result.overall_score,
        suggestions: result.suggestions,
        improved_prompt: result.improved_version?.content || '',
        improved_scores: result.improved_version
          ? result.scores.final_scores
          : {},
        trace_id: result.trace_id,
      };

      const currentHistory = this.evaluationHistorySubject.value;
      const updatedHistory = [historyItem, ...currentHistory].slice(0, 50); // Keep last 50
      this.evaluationHistorySubject.next(updatedHistory);

      // Also save to localStorage
      localStorage.setItem(
        'promptEvaluatorHistory',
        JSON.stringify(updatedHistory)
      );
    } catch (error) {
      console.error('Failed to save to history:', error);
    }
  }

  /**
   * Load history from localStorage
   */
  private loadEvaluationHistory(): void {
    try {
      const savedHistory = localStorage.getItem('promptEvaluatorHistory');
      if (savedHistory) {
        const history = JSON.parse(savedHistory);
        this.evaluationHistorySubject.next(history);
      }
    } catch (error) {
      console.error('Failed to load history from localStorage:', error);
    }
  }

  /**
   * Clear evaluation history
   */
  clearHistory(): void {
    localStorage.removeItem('promptEvaluatorHistory');
    this.evaluationHistorySubject.next([]);
  }

  /**
   * Helper methods
   */
  private capitalizeFirst(text: string): string {
    return text.charAt(0).toUpperCase() + text.slice(1);
  }

  private getDimensionKeywords(dimension: string): string[] {
    const keywordMap: { [key: string]: string[] } = {
      clarity: [
        'clear',
        'understand',
        'confusing',
        'ambiguous',
        'explain',
        'clarify',
      ],
      context: ['context', 'background', 'scope', 'domain', 'environment'],
      relevance: [
        'relevant',
        'related',
        'pertinent',
        'appropriate',
        'applicable',
      ],
      specificity: [
        'specific',
        'detailed',
        'example',
        'concrete',
        'precise',
        'exact',
      ],
      creativity: ['creative', 'innovative', 'original', 'novel', 'unique'],
    };

    return keywordMap[dimension] || [dimension];
  }
}
