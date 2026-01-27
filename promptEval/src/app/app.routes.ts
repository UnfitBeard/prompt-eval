import { Routes } from '@angular/router';
import { LandingPageComponent } from './Components/landing-page/landing-page.component';
import { UserTemplatesComponent } from './Components/user-templates/user-templates.component';
import { PromptEvaluationComponent } from './Components/prompt-eval/prompt-evaluation/prompt-evaluation.component';
import { DashboardComponent } from './Components/dashboard/dashboard.component';
import { AdminDashboardComponent } from './Components/admin/admin-dashboard/admin-dashboard.component';
import { AdminTemplateCreatorComponent } from './Components/admin/admin-template-creator/admin-template-creator.component';
import { AdminProfileComponent } from './Components/admin/admin-profile/admin-profile.component';
import { RegistrationComponent } from './Components/auth/registration/registration.component';
import { LoginComponent } from './Components/auth/login/login.component';
import { AdminSetupComponent } from './Components/auth/admin-setup/admin-setup.component';
import { authGuard } from './Guards/auth.guard';
import { PromptEvidenceComponent } from './Components/prompt-eval/prompt-evidence/prompt-evidence.component';
import { IterationAnalysisComponent } from './Components/iteration-analysis/iteration-analysis.component';
import { PromptEvalV2Component } from './Components/prompt-eval/prompt-eval-v2/prompt-eval-v2.component';
import { ChatbotComponent } from './Components/chatbot/chatbot.component';
import { CourseListComponent } from './Components/courses/course-list/course-list.component';
import { AdminModelsComponent } from './Components/admin/admin-models/admin-models.component';
import { AdminMonitoringComponent } from './Components/admin/admin-monitoring/admin-monitoring.component';
import { AdminTracesComponent } from './Components/admin/admin-traces/admin-traces.component';
import { AdminMaintenanceComponent } from './Components/admin/admin-maintenance/admin-maintenance.component';
import { ScoreHistoryComponent } from './Components/score-history/score-history.component';
import { LeaderboardComponent } from './Components/leaderboard/leaderboard.component';

export const routes: Routes = [
  {
    path: '',
    component: LandingPageComponent,
    data: { hideFooter: true },
  },
  {
    path: 'login',
    component: LoginComponent,
    data: { hideNavbar: true, hideFooter: true },
  },
  {
    path: 'register',
    component: RegistrationComponent,
    data: { hideNavbar: true, hideFooter: true },
  },
  {
    path: 'setup-admin',
    component: AdminSetupComponent,
    data: { hideNavbar: true, hideFooter: true },
  },
  {
    path: 'prompt-evaluation',
    component: PromptEvaluationComponent,
    data: { hideFooter: true },
  },
  {
    path: 'prompt-eval-v2',
    component: PromptEvalV2Component,
    data: { hideFooter: true },
  },
  {
    path: 'chat',
    component: ChatbotComponent,
    title: 'PromptPro Tutor',
    data: { hideFooter: true },
  },
  {
    path: 'courses',
    component: CourseListComponent,
    title: 'Courses List',
    data: { hideFooter: true },
  },
  {
    path: 'trace/:id',
    component: IterationAnalysisComponent,
    data: { hideFooter: true },
  },
  {
    path: 'prompt-evidence',
    component: PromptEvidenceComponent,
    data: { hideFooter: true },
  },
  {
    path: 'user-templates',
    component: UserTemplatesComponent,
    data: { hideFooter: true },
  },
  {
    path: 'dashboard',
    component: DashboardComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'score-history',
    component: ScoreHistoryComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'leaderboard',
    component: LeaderboardComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  { path: 'landing-page', component: LandingPageComponent },
  {
    path: 'admin/admin-dashboard',
    component: AdminDashboardComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'admin/templates',
    component: AdminTemplateCreatorComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'admin/profile',
    component: AdminProfileComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'admin/register',
    component: RegistrationComponent,
    canActivate: [authGuard],
    data: { hideNavbar: true, hideFooter: true, adminRegistration: true },
  },
  {
    path: 'admin/models',
    component: AdminModelsComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'admin/monitoring',
    component: AdminMonitoringComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'admin/traces',
    component: AdminTracesComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
  {
    path: 'admin/maintenance',
    component: AdminMaintenanceComponent,
    canActivate: [authGuard],
    data: { hideFooter: true },
  },
];
