import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

type TemplateCard = {
  title: string;
  description: string;
  domain: 'Software Engineering' | 'Content Writing' | 'Education';
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  rating: number; // 0..5
  uses: number;
};

@Component({
  selector: 'app-user-templates',
  imports: [CommonModule, FormsModule],
  templateUrl: './user-templates.component.html',
  styleUrl: './user-templates.component.css',
})
export class UserTemplatesComponent {
  query = '';
  activeTab: 'Software Engineering' | 'Content Writing' | 'Education' =
    'Software Engineering';
  filters = {
    difficulty: new Set<'Beginner' | 'Intermediate' | 'Advanced'>(),
    useCase: new Set<string>(),
    rating: 0, // 0 = all, 3 = 3+ stars, 4 = 4+ stars, etc.
  };

  readonly tabs: Array<TemplateCard['domain']> = [
    'Software Engineering',
    'Content Writing',
    'Education',
  ];

  // Mock cards matching the screenshot
  cards: TemplateCard[] = [
    {
      title: 'Code Review Template',
      description:
        'A comprehensive template for reviewing code quality and functionality',
      domain: 'Software Engineering',
      difficulty: 'Intermediate',
      rating: 4.8,
      uses: 2345,
    },
    {
      title: 'Blog Post Structure',
      description: 'Structured template for creating engaging blog content',
      domain: 'Content Writing',
      difficulty: 'Beginner',
      rating: 4.5,
      uses: 1890,
    },
    {
      title: 'Lesson Plan Template',
      description: 'Detailed template for creating effective lesson plans',
      domain: 'Education',
      difficulty: 'Intermediate',
      rating: 4.7,
      uses: 1567,
    },
    {
      title: 'Bug Report Template',
      description: 'Standardized template for reporting software bugs',
      domain: 'Software Engineering',
      difficulty: 'Beginner',
      rating: 4.6,
      uses: 3421,
    },
    {
      title: 'Social Media Content',
      description: 'Template for creating engaging social media posts',
      domain: 'Content Writing',
      difficulty: 'Beginner',
      rating: 4.4,
      uses: 2789,
    },
    {
      title: 'Quiz Generation',
      description: 'Template for creating educational quizzes',
      domain: 'Education',
      difficulty: 'Advanced',
      rating: 4.9,
      uses: 1234,
    },
  ];

  get filteredCards(): TemplateCard[] {
    return this.cards
      .filter((c) => c.domain === this.activeTab)
      .filter(
        (c) =>
          !this.query ||
          (c.title + ' ' + c.description)
            .toLowerCase()
            .includes(this.query.toLowerCase())
      )
      .filter(
        (c) =>
          this.filters.difficulty.size === 0 ||
          this.filters.difficulty.has(c.difficulty)
      )
      .filter(
        (c) =>
          (this.filters.rating || 0) === 0 ||
          Math.floor(c.rating) >= this.filters.rating
      );
  }

  toggleSet<T>(set: Set<T>, value: T) {
    set.has(value) ? set.delete(value) : set.add(value);
  }

  copied = false;
  private flashCopied() {
    this.copied = true;
    setTimeout(() => (this.copied = false), 2000);
  }

  private fallbackCopy(text: string) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    try {
      document.execCommand('copy');
      this.flashCopied();
    } finally {
      document.body.removeChild(ta);
    }
  }
  copyTemplate(title: string, description: string) {
    const text = `${title}\n\n${description}`;
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(text).then(() => {
        this.flashCopied();
      });
    } else {
      this.fallbackCopy(text);
    }
  }
}
