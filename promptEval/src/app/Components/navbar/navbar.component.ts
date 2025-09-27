import { CommonModule } from '@angular/common';
import { Component, computed, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../Services/auth.service';

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
  constructor(public authSvc: AuthService) {}

  visibleItems = computed(() =>
    this.items.filter((i) => {
      const logged = this.authSvc.loggedIn();
      if (i.requiresAuth && !logged) return false;
      if (i.guestOnly && logged) return false;
      return true;
    })
  );
}
