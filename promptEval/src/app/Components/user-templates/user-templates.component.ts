import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import {
  PromptsResponse,
  TemplatesService,
} from '../../Services/templates.service';
import { map } from 'rxjs';

type TemplateCard = {
  title: string;
  description: string;
  domain: string;
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

  readonly tabs = [
    'Software Engineering',
    'Content Writing',
    'Education',
  ] as const;

  // Mock cards matching the screenshot
  cards: TemplateCard[] = [];

  constructor(private templateService: TemplatesService) {}

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

  ngOnInit() {
    this.getAllTemplates();
  }

  getAllTemplates() {
    this.templateService.getTemplates().subscribe({
      next: (resp) => {
        this.cards = this.mapToTemplateCards(resp);
      },
      error: (err) => {
        console.error(err);
      },
    });
  }

  mapToTemplateCards(response: PromptsResponse): TemplateCard[] {
    return response.templates.map((tpl) => ({
      title: tpl.title ?? 'Untitled Template',
      description:
        tpl.description ?? 'No description available for this template.',
      domain: this.formatDomain(tpl.domain),
      difficulty: tpl.difficulty as TemplateCard['difficulty'], // ✅ cast
      rating: tpl.stats.avgScore || 0, // backend avgScore is 0..10, UI wants stars (0..5 or 0..10)
      uses: tpl.stats.uses,
    }));
  }

  private formatDomain(domain: string) {
    switch (domain.toLowerCase()) {
      case 'software':
        return 'Software Engineering';
      case 'education':
        return 'Education';
      case 'content':
        return 'Content Writing';
      default:
        return domain;
    }
  }
}
