import { CommonModule } from '@angular/common';
import { Component, computed, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../Services/auth.service';
import { routes } from '../../app.routes';

export type NavItem = {
  label: string;
  href: string;
  requiresAuth?: boolean;
  guestOnly?: boolean;
};

@Component({
  selector: 'app-navbar',
  imports: [RouterLink, CommonModule, FormsModule, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css',
})
export class NavbarComponent {
  @Input({ required: true }) items: NavItem[] = [];
  trackByHref = (_: number, it: NavItem) => it.href;
  constructor(public authSvc: AuthService, public router: Router) {}

  signInOrSignOut(): void {
    if (this.authSvc.loggedIn()) {
      console.log('Loggin out');
      this.authSvc.logout();
    } else {
      console.log(
        `We are at ${this.router
          .getCurrentNavigation()
          ?.extractedUrl?.toString()}`
      );
      this.router.navigateByUrl('/login');
    }
  }

  public buttonText = computed(() => {
    return this.authSvc.loggedIn() ? 'Sign Out' : 'Sign In';
  });

  visibleItems = computed(() =>
    this.items.filter((i) => {
      const logged = this.authSvc.loggedIn();
      if (i.requiresAuth && !logged) return false;
      if (i.guestOnly && logged) return false;
      return true;
    })
  );
}
