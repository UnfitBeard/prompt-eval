import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Clipboard, ClipboardModule } from '@angular/cdk/clipboard';
import {
  PromptsResponse,
  TemplatesService,
} from '../../Services/templates.service';
import { map } from 'rxjs';

type TemplateCard = {
  title: string;
  description: string;
  domain: string;
  content: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  rating: number; // 0..5
  uses: number;
};

type Difficulty = 'Beginner' | 'Intermediate' | 'Advanced';

@Component({
  selector: 'app-user-templates',
  imports: [CommonModule, FormsModule, ClipboardModule],
  templateUrl: './user-templates.component.html',
  standalone: true,
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

  constructor(
    private templateService: TemplatesService,
    private clipboard: Clipboard,
  ) {}

  get filteredCards(): TemplateCard[] {
    return this.cards
      .filter((c) => c.domain === this.activeTab)
      .filter(
        (c) =>
          !this.query ||
          (c.title + ' ' + c.description)
            .toLowerCase()
            .includes(this.query.toLowerCase()),
      )
      .filter(
        (c) =>
          this.filters.difficulty.size === 0 ||
          this.filters.difficulty.has(c.difficulty),
      )
      .filter(
        (c) =>
          (this.filters.rating || 0) === 0 ||
          Math.floor(c.rating) >= this.filters.rating,
      );
  }

  toggleDifficulty(value: Difficulty) {
    // immutable update recommended
    const next = new Set(this.filters.difficulty);
    next.has(value) ? next.delete(value) : next.add(value);
    this.filters.difficulty = next;
  }

  toggleSet<T>(set: Set<T>, value: T) {
    set.has(value) ? set.delete(value) : set.add(value);
  }

  copied = false;
  private flashCopied() {
    this.copied = true;
    setTimeout(() => (this.copied = false), 2000);
  }

  async copyTemplate(title: string, content: string) {
    const text = `${title}\n\n${content}`;
    try {
      const ok = this.clipboard.copy(text);
      if (ok) this.flashCopied();
    } catch (err) {
      console.warn('clipboard copy failed', err);
    }
  }

  ngOnInit() {
    this.getAllTemplates();
  }

  getAllTemplates() {
    this.templateService.getTemplatesList().subscribe({
      next: (resp: any) => {
        console.log('Templates response:', resp);
        this.cards = this.mapToTemplateCards(resp.data);
      },
      error: (err) => {
        console.error(err);
      },
    });
  }

  mapToTemplateCards(response: PromptsResponse): TemplateCard[] {
    return response.templates.map((tpl: any) => ({
      title: tpl.title ?? 'Untitled Template',
      description:
        tpl.description ?? 'No description available for this template.',
      domain: this.formatDomain(tpl.domain),
      content: tpl.content,
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
