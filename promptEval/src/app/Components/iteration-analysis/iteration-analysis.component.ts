import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, Input } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import {
  PromptEvalStateService,
  StoredEval,
} from '../../Services/prompt-eval-state.service';

export interface IterationAnalysis {
  iteration: number;
  overall_score: number;
  base_scores: {
    clarity: number | null;
    context: number | null;
    relevance: number | null;
    specificity: number | null;
    creativity: number | null;
  };
  final_scores: {
    clarity: number | null;
    context: number | null;
    relevance: number | null;
    specificity: number | null;
    creativity: number | null;
  };
  needs_fix_reason?: string;
  llm_missing_fields?: string[]; // if LLM indicated missing info
  llm_evaluation?: any; // optional: first or current iteration
  improve_suggestions?: string[]; // raw suggestions from improve flow
  candidate_adopted?: string; // text of candidate that was adopted
}

@Component({
  selector: 'app-iteration-analysis',
  imports: [CommonModule],
  templateUrl: './iteration-analysis.component.html',
  styleUrl: './iteration-analysis.component.css',
})
export class IterationAnalysisComponent {
  lastTraceId: string | null = null;
  lastTrace: StoredEval | null = null;

  traceId: string | null = null;
  traceData: any = null;
  loading = true;
  error = '';

  constructor(
    private route: ActivatedRoute,
    private http: HttpClient,
    private svcState: PromptEvalStateService
  ) {}

  ngOnInit(): void {
    // get latest trace ID when component loads
    this.lastTraceId = this.svcState.lastTraceId;
    this.traceId = this.route.snapshot.paramMap.get('id');
    this.lastTrace = this.svcState.getSnapshot();

    this.loadTrace();
  }

  openTrace() {
    if (!this.lastTraceId) {
      alert('No trace available.');
      return;
    }

    // open your trace UI page
    window.open(`/trace/${this.lastTraceId}`, '_blank');
  }

  loadTrace() {
    this.http.get(`/trace/${this.traceId}`).subscribe({
      next: (res: any) => {
        this.traceData = res;
        this.loading = false;
      },
      error: () => {
        this.error = 'Trace not found.';
        this.loading = false;
      },
    });
  }
}
