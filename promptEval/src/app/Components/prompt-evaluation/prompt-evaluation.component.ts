import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import {
  PromptEvalService,
  EvaluateResponse,
  RecommendationsResponse,
  RewriteVersion,
  Suggestion,
  ScoresResponse,
} from '../../Services/prompt-eval.service'; // <-- adjust path as needed
import { map, switchMap } from 'rxjs';

interface EvaluationScore {
  label: string;
  score: string;
  color: string;
}

interface Improvement {
  text: string;
}

@Component({
  selector: 'app-prompt-evaluation',
  imports: [FormsModule, CommonModule, RouterLink],
  templateUrl: './prompt-evaluation.component.html',
  styleUrl: './prompt-evaluation.component.css',
})
export class PromptEvaluationComponent {
  private svc = inject(PromptEvalService);
  promptText: string = '';

  loading = false;
  errorMsg: string | null = null;
  overallScore: number | null = null;

  evaluationScores: EvaluationScore[] = [
    { label: 'Clarity', score: '—', color: 'text-amber-500' },
    { label: 'Context', score: '—', color: 'text-blue-500' },
    { label: 'Relevance', score: '—', color: 'text-green-500' },
    { label: 'Specificity', score: '—', color: 'text-purple-500' },
    { label: 'Creativity', score: '—', color: 'text-orange-500' },
  ];
  suggestions: Suggestion[] = [];

  rewriteVersions: RewriteVersion[] = [];

  constructor(private router: Router) {}

  // helper functions
  get overallScorePct(): number {
    return this.overallScore != null
      ? Math.max(0, Math.min(100, this.overallScore * 10))
      : 0;
  }

  private avg(vals: Array<number | null | undefined>): number | null {
    const nums = vals
      .map((v) => (typeof v === 'number' ? v : NaN))
      .filter((v) => Number.isFinite(v)) as number[];
    if (!nums.length) return null;
    return (
      Math.round((nums.reduce((a, b) => a + b, 0) / nums.length) * 10) / 10
    ); // 1 decimal
  }

  private toTenFmt(n: number | null | undefined): string {
    if (n == null || Number.isNaN(n)) return '—';
    const v = Math.max(0, Math.min(10, Number(n)));
    return `${Math.round(v * 10) / 10}/10`;
  }

  private mapScores(resp: ScoresResponse) {
    const mapping: Record<string, number | null | undefined> = {
      Clarity: resp.Clarity,
      Context: resp.Context,
      Creativity: resp.Creativity,
      Specificity: resp.Specificity,
      Relevance: resp.Relevance,
    };

    this.evaluationScores = this.evaluationScores.map((row) => ({
      ...row,
      score: this.toTenFmt(mapping[row.label]),
    }));
    this.overallScore = this.avg([
      resp.Clarity,
      resp.Context,
      resp.Relevance,
      resp.Specificity,
      resp.Creativity,
    ]);
  }

  private mapRecommendation(resp: EvaluateResponse) {
    this.suggestions = Array.isArray(resp.suggestions) ? resp.suggestions : [];
    this.rewriteVersions = Array.isArray(resp.rewriteVersions)
      ? resp.rewriteVersions
      : [];
  }

  handleEvaluate(prompt: string): void {
    const text = (prompt ?? '').trim();
    if (!text) {
      this.errorMsg = 'Please enter a prompt to evaluate';
      return;
    }

    this.errorMsg = null;
    this.loading = true;

    this.handleResultsAndRecommendations(prompt);
  }

  handleApplyRewrite(version: RewriteVersion): void {
    this.promptText = version.content;
  }

  handleRevise(): void {
    console.log('Revising prompt');
  }

  handleSubmitOriginal(): void {
    console.log('Submitting original prompt');
  }

  handleSaveToHistory(): void {
    console.log('Saving to history');
  }

  handleChooseTemplate(): void {
    console.log('Choosing template');
    this.router.navigate(['/user-templates']);
  }

  handleResultsAndRecommendations = async (prompt: string) => {
    this.svc
      .getPromptScores(prompt)
      .pipe(
        map((resp) => {
          this.mapScores(resp);
          return prompt;
        }),
        switchMap((p) => this.svc.evaluatePrompt(p))
      )
      .subscribe({
        next: (resp) => {
          this.mapRecommendation(resp);
          if (resp._error) {
            this.errorMsg =
              'Model result was not strictly JSON; showing partial results';
          }
          this.loading = false;
        },
        error: (err) => {
          this.loading = false;
          this.errorMsg = err.message || 'Evaluation Failed';
        },
      });
  };

  getCardPosition(index: number): string {
    switch (index) {
      case 0:
        return 'left-0';
      case 1:
        return 'left-[419px]';
      case 2:
        return 'left-[837px]';
      default:
        return 'left-0';
    }
  }

  getScorePercentage(score: string): number {
    const numericScore = parseInt(score.split('/')[0]);
    return numericScore * 10;
  }

  getScoreBarColor(score: string): string {
    const numericScore = parseInt(score.split('/')[0]);
    if (numericScore >= 8) return 'bg-green-500';
    if (numericScore >= 6) return 'bg-amber-500';
    return 'bg-red-500';
  }
}
