import { CommonModule } from "@angular/common";
import { Component, signal } from "@angular/core";
import { ActivatedRoute, NavigationEnd, Router, RouterOutlet } from "@angular/router";
import { filter } from "rxjs";
import { FooterComponent } from "./Components/footer/footer.component";
import { NavbarComponent, NavItem } from "./Components/navbar/navbar.component";

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
    // Student Main Features
    {
      label: 'Dashboard',
      href: '/dashboard',
      requiresAuth: true,
      userOnly: true,
    },
    {
      label: 'Evaluate',
      href: '/prompt-eval-v2',
      requiresAuth: true,
      userOnly: true,
    },
    {
      label: 'Template Builder',
      href: '/prompt-evaluation',
      requiresAuth: true,
      userOnly: true,
    },
    {
      label: 'Templates',
      href: '/user-templates',
      requiresAuth: true,
      userOnly: true,
    },
    {
      label: 'Courses',
      href: '/courses',
      requiresAuth: true,
      userOnly: true,
    },
    // Student Analytics
    {
      label: 'My Progress',
      href: '/score-history',
      requiresAuth: true,
      userOnly: true,
    },
    {
      label: 'Leaderboard',
      href: '/leaderboard',
      requiresAuth: true,
      userOnly: true,
    },
    // Admin Features
    {
      label: 'Admin Dashboard',
      href: '/admin/admin-dashboard',
      requiresAuth: true,
      adminOnly: true,
    },
    {
      label: 'Manage Templates',
      href: '/admin/templates',
      requiresAuth: true,
      adminOnly: true,
    },
    {
      label: 'System Monitoring',
      href: '/admin/monitoring',
      requiresAuth: true,
      adminOnly: true,
    },
    {
      label: 'Evaluation Traces',
      href: '/admin/traces',
      requiresAuth: true,
      adminOnly: true,
    },
    {
      label: 'Models & Config',
      href: '/admin/models',
      requiresAuth: true,
      adminOnly: true,
    },
    {
      label: 'Maintenance',
      href: '/admin/maintenance',
      requiresAuth: true,
      adminOnly: true,
    },
    {
      label: 'Admin Profile',
      href: '/admin/profile',
      requiresAuth: true,
      adminOnly: true,
    },
    // General
    {
      label: 'Chat',
      href: '/chat',
    },
  ];

  showNavbar = signal(true);
  showFooter = signal(false);

  constructor(private router: Router, private ar: ActivatedRoute) {
    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd))
      .subscribe(() => {
        let r = this.ar.firstChild;
        while (r?.firstChild) r = r.firstChild;

        const data = r?.snapshot.data ?? {};
        this.showNavbar.set(data['hideNavbar'] !== true);
        this.showFooter.set(data['hideFooter'] === true);
      });
  }
}
