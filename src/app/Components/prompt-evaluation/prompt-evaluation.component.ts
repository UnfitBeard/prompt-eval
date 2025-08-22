import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

interface EvaluationScore {
  label: string;
  score: string;
  color: string;
}

interface Suggestion {
  text: string;
}

interface Improvement {
  text: string;
}

interface RewriteVersion {
  title: string;
  content: string;
  improvements: Improvement[];
}

@Component({
  selector: 'app-prompt-evaluation',
  imports: [FormsModule, CommonModule, RouterLink],
  templateUrl: './prompt-evaluation.component.html',
  styleUrl: './prompt-evaluation.component.css',
})
export class PromptEvaluationComponent {
  promptText: string = '';

  evaluationScores: EvaluationScore[] = [
    { label: 'Clarity', score: '8/10', color: 'text-amber-500' },
    { label: 'Context', score: '7/10', color: 'text-blue-500' },
    { label: 'Relevance', score: '9/10', color: 'text-green-500' },
    { label: 'Specificity', score: '6/10', color: 'text-purple-500' },
    { label: 'Creativity', score: '8/10', color: 'text-orange-500' },
  ];

  suggestions: Suggestion[] = [
    {
      text: 'Consider adding more specific details about the character and their discovery',
    },
    {
      text: 'Add context about the setting and time period',
    },
  ];

  rewriteVersions: RewriteVersion[] = [
    {
      title: 'Enhanced Version',
      content:
        "Write a coming-of-age story about 16-year-old Sarah, who discovers an ancient magical portal in her family's overgrown backyard. The portal leads to a mystical forest where time flows differently, and she must navigate both worlds while keeping her discovery hidden from her skeptical parents.",
      improvements: [
        { text: 'Added specific character details' },
        { text: 'Included setting description' },
        { text: 'Introduced plot elements' },
      ],
    },
    {
      title: 'Alternative Version',
      content:
        'Create a story about a young inventor named Alex who discovers a mysterious portal in their backyard laboratory. The portal connects to a parallel universe where technology and magic coexist, forcing Alex to choose between their normal life and this extraordinary new world.',
      improvements: [
        { text: "Changed character's background" },
        { text: 'Added technological elements' },
        { text: 'Introduced conflict' },
      ],
    },
    {
      title: 'Minimalist Version',
      content:
        'Describe a scene where a character finds a glowing portal in their backyard. The portal emits a soft, warm light and seems to connect to an unknown dimension. The character approaches cautiously, their heart racing with anticipation.',
      improvements: [
        { text: 'Focused on atmosphere' },
        { text: 'Reduced character details' },
        { text: 'Emphasized sensory elements' },
      ],
    },
  ];

  constructor(private router: Router) {}

  handleEvaluate(prompt: string): void {
    console.log('Evaluating prompt:', prompt);
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
