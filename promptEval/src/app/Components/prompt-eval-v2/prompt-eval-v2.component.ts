// components/prompt-evaluator/prompt-evaluator.component.ts
import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  NgModel,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Chart, ChartConfiguration, ChartData, ChartType } from 'chart.js';
import { PromptEvaluatorV2Service } from '../../Service/prompt-evaluator-v2.service';
import {
  PromptEvaluationResult,
  SimilarPrompt,
  ImprovedVersion,
} from '../../models/prompt.model';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { JsonPipe } from '@angular/common';

@Component({
  selector: 'app-prompt-evaluator',
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './prompt-eval-v2.component.html',
  styleUrls: ['./prompt-eval-v2.component.css'],
})
export class PromptEvalV2Component implements OnInit {
  @ViewChild('promptInput') promptInput!: ElementRef;
  @ViewChild('scoreChart') scoreChart!: ElementRef;

  // Form
  evaluationForm: FormGroup;

  // State
  isEvaluating = false;
  evaluationResult: PromptEvaluationResult | null = null;
  errorMessage: string | null = null;
  showAdvancedOptions = false;
  chart: Chart | null = null;

  // Settings
  settings = {
    k: 3,
    improveIfLow: true,
    autoFocus: true,
  };

  // Visualizations
  scoreBreakdown: any = null;
  groupedSuggestions: any[] = [];

  constructor(
    private fb: FormBuilder,
    private evaluatorService: PromptEvaluatorV2Service
  ) {
    this.evaluationForm = this.fb.group({
      prompt: [
        '',
        [
          Validators.required,
          Validators.minLength(10),
          Validators.maxLength(2000),
        ],
      ],
      k: [this.settings.k],
      improveIfLow: [this.settings.improveIfLow],
    });

    // Subscribe to loading state
    this.evaluatorService.loading$.subscribe((loading) => {
      this.isEvaluating = loading;
    });

    // Subscribe to last evaluation
    this.evaluatorService.lastEvaluation$.subscribe((result) => {
      if (result) {
        this.handleEvaluationResult(result);
      }
    });
  }

  ngOnInit(): void {
    // Check API health on init
    this.checkApiHealth();

    // Auto-focus input
    if (this.settings.autoFocus) {
      setTimeout(() => {
        this.promptInput?.nativeElement?.focus();
      }, 100);
    }
  }

  /**
   * Submit form for evaluation
   */
  onSubmit(): void {
    if (this.evaluationForm.invalid) {
      this.markFormGroupTouched(this.evaluationForm);
      return;
    }

    this.errorMessage = null;
    this.evaluationResult = null;

    const formValue = this.evaluationForm.value;

    this.evaluatorService
      .evaluatePrompt(formValue.prompt, formValue.k, formValue.improveIfLow)
      .subscribe({
        error: (error) => {
          this.errorMessage = error.message || 'An unexpected error occurred';
        },
      });
  }

  /**
   * Handle evaluation result
   */
  private handleEvaluationResult(result: PromptEvaluationResult): void {
    this.evaluationResult = result;

    // Generate score breakdown
    this.scoreBreakdown = this.evaluatorService.getScoreSummary(result.scores);

    // Group suggestions by dimension
    this.groupedSuggestions = this.evaluatorService.getGroupedSuggestions(
      result.scores,
      result.suggestions
    );

    // Create/update chart
    this.updateScoreChart();

    // Scroll to results
    setTimeout(() => {
      document
        .getElementById('results-section')
        ?.scrollIntoView({ behavior: 'smooth' });
    }, 300);
  }

  /**
   * Update the radar chart with scores
   */
  private updateScoreChart(): void {
    if (!this.scoreBreakdown || !this.scoreChart) return;

    const ctx = (this.scoreChart.nativeElement as HTMLCanvasElement).getContext(
      '2d'
    );
    if (!ctx) return;

    // Destroy existing chart
    if (this.chart) {
      this.chart.destroy();
    }

    const chartConfig: ChartConfiguration = {
      type: 'radar',
      data: {
        labels: this.scoreBreakdown.labels,
        datasets: [
          {
            label: 'Final Scores',
            data: this.scoreBreakdown.finalValues,
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
            borderColor: 'rgba(54, 162, 235, 1)',
            borderWidth: 2,
            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
          },
          {
            label: 'Base Scores',
            data: this.scoreBreakdown.baseValues,
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            borderColor: 'rgba(255, 99, 132, 1)',
            borderWidth: 1,
            pointBackgroundColor: 'rgba(255, 99, 132, 1)',
            borderDash: [5, 5],
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: true,
        scales: {
          r: {
            beginAtZero: true,
            max: 10,
            min: 0,
            ticks: {
              stepSize: 2,
            },
            pointLabels: {
              font: {
                size: 14,
              },
            },
          },
        },
        plugins: {
          legend: {
            position: 'top',
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                return `${context.dataset.label}: ${context.raw}/10`;
              },
            },
          },
        },
      },
    };

    this.chart = new Chart(ctx, chartConfig);
  }

  /**
   * Use the improved version
   */
  useImprovedVersion(): void {
    if (this.evaluationResult?.improved_version) {
      this.evaluationForm.patchValue({
        prompt: this.evaluationResult.improved_version.content,
      });

      // Re-evaluate automatically
      setTimeout(() => {
        this.onSubmit();
      }, 500);
    }
  }

  /**
   * Copy text to clipboard
   */
  copyToClipboard(text: any): void {
    navigator.clipboard.writeText(JSON.stringify(text)).then(() => {
      // Show success message (you could use a toast service)
      console.log('Copied to clipboard');
    });
  }

  /**
   * Format a timestamp
   */
  formatTime(ms: number): string {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(2)}s`;
  }

  /**
   * Get score color based on value
   */
  getScoreColor(score: number): string {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    if (score >= 4) return 'text-orange-600';
    return 'text-red-600';
  }

  /**
   * Get score badge class
   */
  getScoreBadgeClass(score: number): string {
    if (score >= 8) return 'bg-green-100 text-green-800';
    if (score >= 6) return 'bg-yellow-100 text-yellow-800';
    if (score >= 4) return 'bg-orange-100 text-orange-800';
    return 'bg-red-100 text-red-800';
  }

  /**
   * Check API health
   */
  private checkApiHealth(): void {
    this.evaluatorService.checkHealth().subscribe({
      error: () => {
        this.errorMessage =
          'API server is unavailable. Please make sure the backend is running.';
      },
    });
  }

  /**
   * Helper to mark all form controls as touched
   */
  private markFormGroupTouched(formGroup: FormGroup): void {
    Object.values(formGroup.controls).forEach((control) => {
      control.markAsTouched();
      if (control instanceof FormGroup) {
        this.markFormGroupTouched(control);
      }
    });
  }

  /**
   * Clear form and results
   */
  clearAll(): void {
    this.evaluationForm.reset({
      prompt: '',
      k: this.settings.k,
      improveIfLow: this.settings.improveIfLow,
    });
    this.evaluationResult = null;
    this.errorMessage = null;
    if (this.chart) {
      this.chart.destroy();
      this.chart = null;
    }
  }

  /**
   * View similar prompt details
   */
  viewSimilarPromptDetails(prompt: SimilarPrompt): void {
    // You could implement a modal or expandable section
    console.log('Viewing similar prompt:', prompt);
  }

  /**
   * Toggle advanced options
   */
  toggleAdvancedOptions(): void {
    this.showAdvancedOptions = !this.showAdvancedOptions;
  }
}
