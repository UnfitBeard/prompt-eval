import { Routes } from '@angular/router';
import { LandingPageComponent } from './Components/landing-page/landing-page.component';
import { UserTemplatesComponent } from './Components/user-templates/user-templates.component';
import { PromptEvaluationComponent } from './Components/prompt-evaluation/prompt-evaluation.component';
import { DashboardComponent } from './Components/dashboard/dashboard.component';
import { AdminDashboardComponent } from './Components/admin-dashboard/admin-dashboard.component';
import { AdminTemplateCreatorComponent } from './Components/admin-template-creator/admin-template-creator.component';
import { AdminProfileComponent } from './Components/admin-profile/admin-profile.component';
import { RegistrationComponent } from './Components/registration/registration.component';
import { LoginComponent } from './Components/login/login.component';

export const routes: Routes = [
  { path: '', component: LandingPageComponent },
  { path: 'login', component: LoginComponent },
  { path: 'register', component: RegistrationComponent },
  { path: 'prompt-evaluation', component: PromptEvaluationComponent },
  { path: 'user-templates', component: UserTemplatesComponent },
  { path: 'dashboard', component: DashboardComponent },
  { path: 'landing-page', component: LandingPageComponent },
  { path: 'admin/admin-dashboard', component: AdminDashboardComponent },
  { path: 'admin/templates', component: AdminTemplateCreatorComponent },
  { path: 'admin/profile', component: AdminProfileComponent },
];
