import { Routes } from '@angular/router';
import { LandingPageComponent } from './Components/landing-page/landing-page.component';
import { UserTemplatesComponent } from './Components/user-templates/user-templates.component';
import { PromptEvaluationComponent } from './Components/prompt-evaluation/prompt-evaluation.component';
import { DashboardComponent } from './Components/dashboard/dashboard.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'prompt-evaluation', component: PromptEvaluationComponent },
  { path: 'user-templates', component: UserTemplatesComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'landing-page', component: LandingPageComponent },
];
