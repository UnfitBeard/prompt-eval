import { Component, signal } from '@angular/core';
import {
  ActivatedRoute,
  NavigationEnd,
  Router,
  RouterOutlet,
} from '@angular/router';
import { PromptEvaluationComponent } from './Components/prompt-evaluation/prompt-evaluation.component';
import { UserTemplatesComponent } from './Components/user-templates/user-templates.component';
import { NavbarComponent, NavItem } from './Components/navbar/navbar.component';
import { FooterComponent } from './Components/footer/footer.component';
import { filter } from 'rxjs';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavbarComponent, FooterComponent, CommonModule],
  standalone: true,
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  title = 'promptEval';
  navigationItems: NavItem[] = [
    { label: 'Dashboard', href: '/dashboard' },
    // { label: 'Landing page', href: '/landing-page' },
    // { label: 'PromptEvaluation', href: '/prompt-evaluation' },
    { label: 'Prompt Evaluation', href: '/prompt-eval-v2' },
    { label: 'PromptEvidence', href: '/prompt-evidence' },
    { label: 'Templates', href: '/user-templates' },
    { label: 'Chat', href: '/chat' },
    { label: 'Courses', href: '/courses' },
  ];

  showNavbar = signal(true);
  showFooter = signal(false);

  constructor(private router: Router, private ar: ActivatedRoute) {
    this.router.events
      .pipe(filter((e) => e instanceof NavigationEnd))
      .subscribe(() => {
        let r = this.ar.firstChild;
        while (r?.firstChild) r = r.firstChild;
        const data = r?.snapshot.data ?? {};
        this.showNavbar.set(!data['hideNavbar']);
        this.showFooter.set(!data['hideFooter']);
      });
  }
}
