import { CommonModule } from '@angular/common';
import { Component, computed, Input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../Service/auth.service';
import { User, UserRole } from '../../models/course.model';

export type NavItem = {
  label: string;
  href: string;
  requiresAuth?: boolean;
  guestOnly?: boolean;
  adminOnly?: boolean;
  userOnly?: boolean;
  instructorOnly?: boolean;
};

@Component({
  selector: 'app-navbar',
  imports: [RouterLink, CommonModule, FormsModule, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css',
})
export class NavbarComponent {
  @Input({ required: true }) items: NavItem[] = [];

  private userSig = signal<User | null>(null);

  constructor(public authSvc: AuthService, public router: Router) {
    this.authSvc.currentUser$.subscribe(user => {
      this.userSig.set(user);
    });
  }

  trackByHref = (_: number, it: NavItem) => it.href;

  buttonText = computed(() =>
    this.authSvc.loggedIn() ? 'Sign Out' : 'Sign In'
  );

  /** 🔥 THIS IS THE FIX */
  visibleItems = computed(() => {
    const logged = this.authSvc.loggedIn();
    const user = this.userSig();
    const role = user?.role ?? null;

    return this.items.filter(i => {
      if (i.requiresAuth && !logged) return false;
      if (i.guestOnly && logged) return false;

      // --- ROLE-EXCLUSIVE UI LOGIC ---
      if (role === UserRole.ADMIN) {
        return i.adminOnly || (!i.userOnly && !i.instructorOnly && !i.adminOnly);
      }

      if (role === UserRole.STUDENT) {
        return i.userOnly || (!i.adminOnly && !i.instructorOnly && !i.userOnly);
      }

      if (role === UserRole.INSTRUCTOR) {
        return i.instructorOnly || (!i.adminOnly && !i.userOnly && !i.instructorOnly);
      }

      // Guest
      return !i.requiresAuth;
    });
  });

  signInOrSignOut(): void {
    if (this.authSvc.loggedIn()) {
      this.authSvc.logout();
    } else {
      this.router.navigateByUrl('/login');
    }
  }
}
