import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';

type Feature = {
  icon: 'spark' | 'shield' | 'clock' | 'target' | 'chart' | 'bolt';
  title: string;
  desc: string;
};
type Step = { icon: 'one' | 'two' | 'three'; title: string; desc: string };
type Plan = {
  badge?: string;
  name: string;
  price: string;
  period?: string;
  cta: string;
  features: string[];
  highlight?: boolean;
};
type FooterCol = { heading: string; links: { label: string; href: string }[] };

@Component({
  selector: 'app-landing-page',
  imports: [FormsModule, CommonModule],
  templateUrl: './landing-page.component.html',
  styleUrl: './landing-page.component.css',
})
export class LandingPageComponent {
  hero = {
    eyebrow: 'promptEval',
    title: 'Evaluate and Perfect Your AI Prompts',
    desc: 'Get instant quality scores, concrete suggestions, and ready-to-use rewrites—so your prompts perform reliably every time.',
    primaryCta: 'Start Free',
    secondaryCta: 'View Templates',
    highlight: {
      title: 'Why teams choose promptEval',
      points: [
        'Objective metrics for clarity, context, and specificity',
        'Versioning and history for quick A/B comparisons',
        'Works with any LLM—no lock-in',
      ],
    },
  };

  // Features
  features: Feature[] = [
    {
      icon: 'spark',
      title: 'Prompt Analyzer',
      desc: 'Automatic scores + suggestions for every prompt.',
    },
    {
      icon: 'target',
      title: 'Template Library',
      desc: 'Expert templates for common tasks and domains.',
    },
    {
      icon: 'clock',
      title: 'One-click Rewrites',
      desc: 'Generate concise, improved alternatives instantly.',
    },
    {
      icon: 'chart',
      title: 'Benchmark Metrics',
      desc: 'Track scores over time and spot regressions.',
    },
    {
      icon: 'shield',
      title: 'Team Controls',
      desc: 'Roles, approvals, and audit-friendly history.',
    },
    {
      icon: 'bolt',
      title: 'Fast & Lightweight',
      desc: 'No SDKs required—works with your current stack.',
    },
  ];

  // How it works
  steps: Step[] = [
    {
      icon: 'one',
      title: 'Paste or pick a template',
      desc: 'Start from scratch or select a best-practice template.',
    },
    {
      icon: 'two',
      title: 'Evaluate instantly',
      desc: 'Get quality scores and concrete improvement tips.',
    },
    {
      icon: 'three',
      title: 'Apply & ship',
      desc: 'Accept a rewrite, export, or save for your team.',
    },
  ];

  // Logos / companies (simple monogram chips)
  companies = ['Acme', 'Globex', 'Infinisoft', 'Nova AI', 'Kite Labs', 'Aster'];

  // Pricing
  plans: Plan[] = [
    {
      name: 'Starter',
      price: '$0',
      period: '/mo',
      cta: 'Get Started',
      features: [
        '100 evaluations / mo',
        'Core metrics (clarity, context)',
        'Basic templates',
        'Exports (copy / paste)',
      ],
    },
    {
      badge: 'Most Popular',
      name: 'Pro',
      price: '$19',
      period: '/mo',
      cta: 'Upgrade to Pro',
      highlight: true,
      features: [
        'Unlimited evaluations',
        'All metrics + rewrite suggestions',
        'Versioning & history',
        'Team sharing (up to 5 seats)',
        'Email support',
      ],
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      cta: 'Contact Sales',
      features: [
        'SSO & role-based access',
        'Private templates & approvals',
        'On-prem or VPC options',
        'Security review & SLA',
        'Dedicated success manager',
      ],
    },
  ];

  // Footer
  footerCols: FooterCol[] = [
    {
      heading: 'Product',
      links: [
        { label: 'Features', href: '#' },
        { label: 'Templates', href: '#' },
        { label: 'Pricing', href: '#' },
      ],
    },
    {
      heading: 'Resources',
      links: [
        { label: 'Guides', href: '#' },
        { label: 'API Reference', href: '#' },
        { label: 'Support', href: '#' },
      ],
    },
    {
      heading: 'Company',
      links: [
        { label: 'About', href: '#' },
        { label: 'Blog', href: '#' },
        { label: 'Careers', href: '#' },
      ],
    },
  ];

  // Helpers
  initials(name: string, max = 2): string {
    if (!name) return '';
    return name
      .trim()
      .split(/\s+/)
      .map((w) => w[0] ?? '')
      .join('')
      .slice(0, max)
      .toUpperCase();
  }

  currentYear = new Date().getFullYear();
}
