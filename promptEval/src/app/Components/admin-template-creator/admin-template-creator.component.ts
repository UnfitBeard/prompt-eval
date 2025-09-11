import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Difficulty = 'Beginner' | 'Intermediate' | 'Advanced';

type Domain = {
  key: 'software' | 'education' | 'content';
  label: string;
  desc: string;
  icon: 'code' | 'book' | 'pen';
};

type Category = {
  key:
    | 'code-review'
    | 'documentation'
    | 'bug-report'
    | 'lesson-plan'
    | 'blog-post';
  label: string;
  desc: string;
  domain: Domain['key'];
};

type Metric = { key: string; label: string; desc: string; value: number }; // 0..10

@Component({
  selector: 'app-admin-template-creator',
  imports: [CommonModule, FormsModule],
  templateUrl: './admin-template-creator.component.html',
  styleUrl: './admin-template-creator.component.css',
})
export class AdminTemplateCreatorComponent {
  // ---------------- DATA (page-controlled) ----------------
  title = 'Create New Prompt Template';
  subtitle = 'Design and standardize your prompt template';

  domains: Domain[] = [
    {
      key: 'software',
      label: 'Software Engineering',
      desc: 'Code reviews, documentation, testing templates',
      icon: 'code',
    },
    {
      key: 'education',
      label: 'Education',
      desc: 'Lesson plans and assessment creator',
      icon: 'book',
    },
    {
      key: 'content',
      label: 'Content Writing',
      desc: 'Blog posts, social media & emails',
      icon: 'pen',
    },
  ];

  difficulties: Difficulty[] = ['Beginner', 'Intermediate', 'Advanced'];

  categories: Category[] = [
    {
      key: 'code-review',
      label: 'Code Review',
      desc: 'Ensure maintainability & quality',
      domain: 'software',
    },
    {
      key: 'documentation',
      label: 'Documentation',
      desc: 'Create clear & accurate docs',
      domain: 'software',
    },
    {
      key: 'bug-report',
      label: 'Bug Report',
      desc: 'Standardize issue triage details',
      domain: 'software',
    },
    {
      key: 'lesson-plan',
      label: 'Lesson Plan',
      desc: 'Create an effective lesson outline',
      domain: 'education',
    },
    {
      key: 'blog-post',
      label: 'Blog Post',
      desc: 'Structure for engaging articles',
      domain: 'content',
    },
  ];

  // Evaluation preview (read-only demo)
  metrics: Metric[] = [
    {
      key: 'clarity',
      label: 'Clarity',
      desc: 'Clear and understandable',
      value: 8.4,
    },
    {
      key: 'context',
      label: 'Context',
      desc: 'Includes relevant context',
      value: 8.1,
    },
    {
      key: 'relevance',
      label: 'Relevance',
      desc: 'Targets expected outcome',
      value: 8.7,
    },
    {
      key: 'specificity',
      label: 'Specificity',
      desc: 'Explicit instructions',
      value: 7.6,
    },
    {
      key: 'creativity',
      label: 'Creativity',
      desc: 'Encourages unique responses',
      value: 7.9,
    },
  ];

  proTips: string[] = [
    'State the objective and your requirements.',
    'Give constraints (tone, format, length).',
    'Provide one concrete example.',
    'List the deliverables and success criteria.',
  ];

  // ---------------- FORM STATE ----------------
  form = {
    domain: null as Domain['key'] | null,
    difficulty: 'Beginner' as Difficulty,
    category: null as Category['key'] | null,
    prompt: '',
    includeEval: true,
  };

  // ---------------- COMPUTED ----------------
  get categoriesForDomain(): Category[] {
    return this.form.domain
      ? this.categories.filter((c) => c.domain === this.form.domain)
      : this.categories;
  }

  get canCreate(): boolean {
    return !!(
      this.form.domain &&
      this.form.category &&
      this.form.prompt.trim().length >= 20
    );
  }

  get promptChars(): number {
    return this.form.prompt.trim().length;
  }

  metricWidth(v: number): string {
    const pct = Math.max(0, Math.min(100, Math.round((v / 10) * 100)));
    return pct + '%';
  }

  // ---------------- ACTIONS ----------------
  selectDomain(key: Domain['key']): void {
    this.form.domain = key;
  }
  selectDifficulty(d: Difficulty): void {
    this.form.difficulty = d;
  }
  selectCategory(key: Category['key']): void {
    this.form.category = key;
  }

  createTemplate(): void {
    if (!this.canCreate) return;
    const payload = {
      ...this.form,
      createdAt: new Date().toISOString(),
    };
    console.log('CREATE TEMPLATE →', payload);
    alert('Template created! (see console for payload)');
  }

  saveDraft(): void {
    const draft = { ...this.form, savedAt: new Date().toISOString() };
    console.log('SAVE DRAFT →', draft);
    alert('Draft saved! (see console)');
  }

  prev(): void {
    console.log('Prev step');
  }
  next(): void {
    console.log('Next step');
  }
}
