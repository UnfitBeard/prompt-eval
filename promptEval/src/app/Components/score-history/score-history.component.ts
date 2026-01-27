// Components/score-history/score-history.component.ts
import { CommonModule } from '@angular/common';
import { Component, OnInit, inject } from '@angular/core';
import { PromptScoresService, ScoreHistoryEntry } from '../../Service/prompt-scores.service';

@Component({
  selector: 'app-score-history',
  imports: [CommonModule],
  templateUrl: './score-history.component.html',
  styleUrl: './score-history.component.css',
})
export class ScoreHistoryComponent implements OnInit {
  private promptScoresService = inject(PromptScoresService);
  
  loading = true;
  error: string | null = null;
  scores: ScoreHistoryEntry[] = [];
  
  // Chart data
  chartLabels: string[] = [];
  chartData: number[] = [];
  chartMax = 10;

  ngOnInit() {
    this.loadScoreHistory();
  }

  loadScoreHistory() {
    this.loading = true;
    this.error = null;

    this.promptScoresService.getScoreHistory(50).subscribe({
      next: (scores) => {
        this.scores = scores;
        this.prepareChartData(scores);
        this.loading = false;
      },
      error: (err) => {
        console.error('Error loading score history:', err);
        this.error = 'Failed to load score history';
        this.loading = false;
      },
    });
  }

  private prepareChartData(scores: ScoreHistoryEntry[]) {
    // Sort by timestamp (oldest first for chart)
    const sorted = [...scores].sort((a, b) => 
      new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    );

    this.chartLabels = sorted.map((s, i) => {
      const date = new Date(s.timestamp);
      return `${date.getMonth() + 1}/${date.getDate()}`;
    });

    this.chartData = sorted.map(s => s.overall_score);
    
    // Set max to 10 or slightly above max value
    this.chartMax = Math.max(10, Math.max(...this.chartData) * 1.1);
  }

  getChartPath(): string {
    if (this.chartData.length === 0) return '';

    const width = 600;
    const height = 200;
    const padding = 40;
    const innerWidth = width - padding * 2;
    const innerHeight = height - padding * 2;

    const stepX = innerWidth / Math.max(1, this.chartData.length - 1);
    
    const points = this.chartData.map((value, index) => {
      const x = padding + index * stepX;
      const y = padding + innerHeight - (value / this.chartMax) * innerHeight;
      return `${index === 0 ? 'M' : 'L'} ${x} ${y}`;
    });

    return points.join(' ');
  }

  Math = Math;

  getTrend(): { direction: 'up' | 'down' | 'stable'; percentage: number } {
    if (this.chartData.length < 2) {
      return { direction: 'stable', percentage: 0 };
    }

    const first = this.chartData[0];
    const last = this.chartData[this.chartData.length - 1];
    const change = ((last - first) / first) * 100;

    if (Math.abs(change) < 1) {
      return { direction: 'stable', percentage: 0 };
    }

    return {
      direction: change > 0 ? 'up' : 'down',
      percentage: Math.abs(change),
    };
  }

  getAverageScore(): number {
    if (this.chartData.length === 0) return 0;
    const sum = this.chartData.reduce((a, b) => a + b, 0);
    return sum / this.chartData.length;
  }

  getCircleX(index: number): number {
    return 40 + (index * (520 / Math.max(1, this.chartData.length - 1)));
  }

  getCircleY(value: number): number {
    return 40 + (160 - (value / this.chartMax) * 120);
  }

  getLabelX(index: number): number {
    return 40 + (index * (520 / Math.max(1, this.chartLabels.length - 1)));
  }
}

