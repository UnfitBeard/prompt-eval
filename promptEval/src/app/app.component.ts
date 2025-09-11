import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { PromptEvaluationComponent } from './Components/prompt-evaluation/prompt-evaluation.component';
import { UserTemplatesComponent } from './Components/user-templates/user-templates.component';
import { NavbarComponent, NavItem } from './Components/navbar/navbar.component';
import { FooterComponent } from './Components/footer/footer.component';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavbarComponent, FooterComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  title = 'promptEval';
  navigationItems: NavItem[] = [
    { label: 'Dashboard', href: '/dashboard' },
    // { label: 'Landing page', href: '/landing-page' },
    { label: 'PromptEvaluation', href: '/prompt-evaluation' },
    { label: 'Templates', href: '/user-templates' },
    { label: 'Settings', href: '/settings' },
  ];
}
