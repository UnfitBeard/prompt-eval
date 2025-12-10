import { Injectable } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import type { ScoresResponse } from './prompt-eval.service';

export interface StoredEval {
  promptText?: string;
  form?: any;
  scoresResponse?: ScoresResponse | null;
  retrieved?: any[]; // top_rag_prompts or similar
  llmEvaluation?: any | null; // parsed LLM JSON
  timestamp?: string;
  trace_id: string;
}

const SESSION_KEY = 'prompt_eval_last';

@Injectable({ providedIn: 'root' })
export class PromptEvalStateService {
  private _last = new BehaviorSubject<StoredEval | null>(
    this._loadFromSession()
  );
  public last$ = this._last.asObservable();

  /** Get immediate snapshot (synchronous) */
  getSnapshot(): StoredEval | null {
    return this._last.getValue();
  }

  /** Save full response into the service + sessionStorage */
  setLastResponse(payload: StoredEval) {
    const item = {
      ...this.getSnapshot(),
      ...payload,
      timestamp: new Date().toISOString(),
    };
    this._last.next(item);
    try {
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(item));
    } catch (e) {
      // ignore if storage unavailable
      console.warn('PromptEvalStateService: sessionStorage write failed', e);
    }
  }

  get lastTraceId(): string | null {
    return this._last.getValue()?.trace_id || null;
  }

  /** Clear stored state */
  clear() {
    this._last.next(null);
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch (e) {}
  }

  private _loadFromSession(): StoredEval | null {
    try {
      const raw = sessionStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (e) {
      return null;
    }
  }
}
