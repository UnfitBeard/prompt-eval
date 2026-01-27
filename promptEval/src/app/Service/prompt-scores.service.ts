// Service/prompt-scores.service.ts
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

export interface ScoreEntry {
  prompt: string;
  overall_score: number;
  scores: Record<string, number>;
  trace_id?: string;
  timestamp?: string;
}

export interface ScoreHistoryEntry {
  id: string;
  prompt: string;
  overall_score: number;
  scores: Record<string, number>;
  timestamp: string;
}

@Injectable({
  providedIn: 'root',
})
export class PromptScoresService {
  constructor(private api: ApiService) {}

  saveScore(entry: ScoreEntry): Observable<{ score_id: string }> {
    return this.api.post<{ score_id: string }>('/prompt-scores/save', entry);
  }

  getScoreHistory(limit: number = 50): Observable<ScoreHistoryEntry[]> {
    return this.api.get<ScoreHistoryEntry[]>('/prompt-scores/history', { limit });
  }
}

