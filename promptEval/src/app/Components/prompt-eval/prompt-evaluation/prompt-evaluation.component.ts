import { CommonModule } from '@angular/common';
import { Component, inject, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import {
  PromptEvalService,
  EvaluateResponse,
  RecommendationsResponse,
  RewriteVersion,
  Suggestion,
  ScoresResponse,
} from '../../../Services/prompt-eval.service'; // <-- adjust path as needed
import { map, switchMap } from 'rxjs';
import { PromptEvalStateService } from '../../../Services/prompt-eval-state.service';
import { CourseService } from '../../../Service/course.service';
import { PromptScoresService } from '../../../Service/prompt-scores.service';

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
  imports: [FormsModule, CommonModule],
  templateUrl: './prompt-evaluation.component.html',
  styleUrl: './prompt-evaluation.component.css',
})
export class PromptEvaluationComponent {
  toggleForms() {
    this.showForm1 = !this.showForm1;
  }
  showForm1: boolean = true;
  private svc = inject(PromptEvalService);
  private svcState = inject(PromptEvalStateService);
  private courseService = inject(CourseService);
  private promptScoresService = inject(PromptScoresService);
  promptText: string = '';
  xpAwarded: number | null = null;

  loading = false;
  errorMsg: string | null = null;
  overallScore: number | null = null;

  // Structured form model
  form: any = {
    domain: 'software_engineering',
    subtype: '',
    title: '',
    audience: '',
    purpose: '',
    keyPoints: '',
    outputFormat: 'plain',
    tech: '',
    lengthTarget: '',
    tone: 'neutral',
    example: '',
    acceptance: '',
    constraints: '',
  };

  evaluationScores: EvaluationScore[] = [
    { label: 'Clarity', score: '—', color: 'text-amber-500' },
    { label: 'Context', score: '—', color: 'text-blue-500' },
    { label: 'Relevance', score: '—', color: 'text-green-500' },
    { label: 'Specificity', score: '—', color: 'text-purple-500' },
    { label: 'Creativity', score: '—', color: 'text-orange-500' },
  ];
  suggestions: Suggestion[] = [];

  rewriteVersions: RewriteVersion[] = [];

  constructor(public router: Router) {}

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
      Clarity: resp.scores.final_scores.clarity,
      Context: resp.scores.final_scores.context,
      Creativity: resp.scores.final_scores.creativity,
      Specificity: resp.scores.final_scores.specificity,
      Relevance: resp.scores.final_scores.relevance,
    };

    this.evaluationScores = this.evaluationScores.map((row) => ({
      ...row,
      score: this.toTenFmt(mapping[row.label]),
    }));
    this.overallScore = this.avg([
      resp.scores.final_scores.clarity,
      resp.scores.final_scores.context,
      resp.scores.final_scores.relevance,
      resp.scores.final_scores.specificity,
      resp.scores.final_scores.creativity,
    ]);
  }

  private mapRecommendation(resp: ScoresResponse) {
    this.suggestions = Array.isArray(resp.llm_evaluation?.suggestions)
      ? resp.llm_evaluation.suggestions
      : [];
    this.rewriteVersions = Array.isArray(resp.llm_evaluation?.rewriteVersions)
      ? resp.llm_evaluation.rewriteVersions
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

  handleResultsAndRecommendations(prompt: string): void {
    console.log(`Sending prompt: ${prompt}`);
    this.svc
      .getPromptScores(prompt) // Observable<ScoresResponse>
      .subscribe({
        next: (resp: ScoresResponse) => {
          console.log('Scores response:', resp);
          this.mapScores(resp);
          this.mapRecommendation(resp);

          // NEW: persist richer state
          this.svcState.setLastResponse({
            promptText: prompt, // raw prompt text you evaluated
            form: this.form, // structured form content
            scoresResponse: resp, // server ScoresResponse object
            retrieved: (resp as any).top_rag_prompts || null, // optional
            llmEvaluation: (resp as any).llm_evaluation || null,
            // NEW — capture trace id
            trace_id: (resp as any).trace_id || null,
          });

          // Award XP based on overall score
          this.awardXP(this.overallScore);

          // Save score to history
          this.saveScoreToHistory(prompt, resp);

          this.loading = false;
        },
        error: (err) => {
          this.loading = false;
          this.errorMsg = err.message || 'Evaluation Failed';
        },
      });
  }

  private awardXP(score: number | null): void {
    if (score === null || score === undefined) return;

    // Calculate XP based on score (0-10 scale)
    // Higher scores get more XP: 10 = 100 XP, 9 = 90 XP, etc.
    // Minimum 10 XP for any evaluation
    const xpAmount = Math.max(10, Math.round(score * 10));

    this.courseService.addXp(xpAmount, `Prompt evaluation (score: ${score.toFixed(1)})`).subscribe({
      next: (result) => {
        this.xpAwarded = xpAmount;
        console.log(`Awarded ${xpAmount} XP. Total XP: ${result.total_xp}`);
        // Clear the notification after 5 seconds
        setTimeout(() => {
          this.xpAwarded = null;
        }, 5000);
      },
      error: (err) => {
        console.error('Failed to award XP:', err);
      },
    });
  }

  private saveScoreToHistory(prompt: string, resp: ScoresResponse): void {
    const traceId = (resp as any).trace_id || null;
    // Ensure all scores are numbers (not null)
    const scores: Record<string, number> = {
      clarity: resp.scores.final_scores.clarity ?? 0,
      context: resp.scores.final_scores.context ?? 0,
      relevance: resp.scores.final_scores.relevance ?? 0,
      specificity: resp.scores.final_scores.specificity ?? 0,
      creativity: resp.scores.final_scores.creativity ?? 0,
    };

    this.promptScoresService.saveScore({
      prompt,
      overall_score: this.overallScore || 0,
      scores,
      trace_id: traceId,
    }).subscribe({
      next: () => {
        console.log('Score saved to history');
      },
      error: (err) => {
        console.error('Failed to save score to history:', err);
      },
    });
  }

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
    const raw = (score || '').split('/')[0];
    const base = parseFloat(raw);
    if (!Number.isFinite(base)) return 0;
    return Math.max(0, Math.min(100, base * 10));
  }

  getScoreBarColor(score: string): string {
    const raw = (score || '').split('/')[0];
    const base = parseFloat(raw);
    if (!Number.isFinite(base)) return 'bg-gray-300';
    if (base >= 8) return 'bg-green-500';
    if (base >= 6) return 'bg-amber-500';
    if (base >= 4) return 'bg-violet-500';
    return 'bg-red-500';
  }

  /** Build a human-readable prompt from the structured form. */
  private buildPromptFromForm(): string {
    const f = this.form;
    const parts: string[] = [];

    // Header: task and goal
    parts.push(`Task: ${this.humanReadableSubtype(f.domain, f.subtype)}.`);
    if (f.title) parts.push(`Title: ${f.title}.`);
    if (f.purpose) parts.push(`Purpose: ${f.purpose}.`);
    if (f.audience) parts.push(`Target audience: ${f.audience}.`);

    // Domain & tech
    parts.push(`Domain: ${this.humanReadableDomain(f.domain)}.`);
    if (f.tech) parts.push(`Preferred tech/language: ${f.tech}.`);

    // Format & length
    parts.push(`output format: ${this.formatLabel(f.outputFormat)}.`);
    if (f.lengthTarget) parts.push(`Length target: ${f.lengthTarget}.`);
    parts.push(`Tone/style: ${f.tone}.`);

    // Key points and example
    if (f.keyPoints) parts.push(`key points: ${f.keyPoints}.`);
    if (f.example) parts.push(`Example input: ${f.example}.`);
    // Acceptance & constraints
    if (f.acceptance) {
      parts.push(`Acceptance criteria: ${f.acceptance}.`);
    } else {
      parts.push(``);
    }
    if (f.constraints) parts.push(`Constraints: ${f.constraints}.`);

    // // Acceptance & constraints
    // if (f.acceptance) {
    //   parts.push(`Acceptance criteria (must be satisfied): ${f.acceptance}.`);
    // } else {
    //   parts.push(
    //     `Acceptance criteria: ensure the output covers all requested sections and keys.`
    //   );
    // }
    // if (f.constraints) parts.push(`Constraints: ${f.constraints}.`);

    // // Instruction for completeness & validation
    // parts.push(
    //   'Produce the requested output exactly matching the desired format. ' +
    //     'Then run a self-check against the acceptance criteria and annotate any missing items. ' +
    //     'If items are missing, retry once to correct the output. Output the final result only if it passes the acceptance criteria.'
    // );

    return parts.join(' ');
  }

  private humanReadableDomain(domain: string): string {
    switch (domain) {
      case 'software_engineering':
        return 'Software engineering';
      case 'content_creation':
        return 'Content creation';
      case 'education':
        return 'Education';
      default:
        return domain || 'General';
    }
  }

  private humanReadableSubtype(domain: string, subtype: string): string {
    // map subtypes to friendly strings
    const map: any = {
      software_engineering: {
        full_stack_app: 'full-stack application (frontend + backend + DB)',
        backend_api: 'backend API / microservice',
        cli_tool: 'CLI tool or script',
        unit_tests: 'unit tests and test plan',
        refactor_plan: 'refactor plan / architecture notes',
      },
      content_creation: {
        blog_post: 'blog post or article',
        social_post_series: 'social media post series',
        video_script: 'video script',
        newsletter: 'newsletter issue',
      },
      education: {
        lesson_plan: 'lesson plan',
        quiz: 'quiz with answer key',
        summary: 'topic summary',
        exercise_set: 'exercise set with solutions',
      },
    };
    return (map[domain] && map[domain][subtype]) || subtype || 'task';
  }

  private formatLabel(fmt: string): string {
    const m: any = {
      plain: 'Plain text',
      markdown: 'Markdown',
      json: 'JSON',
      html: 'HTML',
      code: 'Source code',
    };
    return m[fmt] || fmt;
  }

  /** Called by the structured form Evaluate button. */
  assemblePromptAndEvaluate(): void {
    let finalPrompt: string = '';
    if (this.showForm1) {
      finalPrompt = this.buildPromptFromForm();
      this.promptText = finalPrompt;
      // clear old results while loading
    } else {
      finalPrompt = this.promptText;
      this.promptText = finalPrompt;
    }
    // clear old results while loading
    this.loading = true;
    this.errorMsg = null;
    this.handleResultsAndRecommendations(finalPrompt);
  }

  get template() {
    return this;
  }

  /** Reset the form to default values. */
  resetForm(): void {
    this.form = {
      domain: 'software_engineering',
      subtype: 'full_stack_app',
      title: '',
      audience: '',
      purpose: '',
      keyPoints: '',
      outputFormat: 'plain',
      tech: '',
      lengthTarget: '',
      tone: 'neutral',
      example: '',
      acceptance: '',
      constraints: '',
    };
    this.promptText = '';
    this.evaluationScores = this.evaluationScores.map((s) => ({
      ...s,
      score: '—',
    }));
    this.rewriteVersions = [];
    this.suggestions = [];
    this.overallScore = null;
    this.errorMsg = null;
  }

  ngOnInit() {
    this.lastTraceId = this.svcState.lastTraceId;
    const snapshot = this.svcState.getSnapshot();
    if (snapshot) {
      if (snapshot.promptText) this.promptText = snapshot.promptText;
      if (snapshot.form) this.form = { ...this.form, ...snapshot.form };
      if (snapshot.scoresResponse) {
        this.mapScores(snapshot.scoresResponse);
        this.mapRecommendation(snapshot.scoresResponse);
      }
    }

    // live updates (optional)
    this.svcState.last$.subscribe((val) => {
      if (!val) return;
      // update UI when state changes elsewhere
      if (val.promptText && val.promptText !== this.promptText)
        this.promptText = val.promptText;
    });
  }

  lastTraceId: string | null = null;

  openTrace() {
    if (!this.lastTraceId) {
      alert('No trace available.');
      return;
    }

    // open your trace UI page
    window.open(`/trace/${this.lastTraceId}`, '_blank');
  }
}
