import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink, RouterLinkActive } from '@angular/router';

export type NavItem = {
  label: string;
  href: string;
};

@Component({
  selector: 'app-navbar',
  imports: [RouterLink, CommonModule, FormsModule, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css',
})
export class NavbarComponent {
  @Input() items: NavItem[] = [];

  navigationItems: NavItem[] = [
    { label: 'Dashboard', href: '/dashboard' },
    { label: 'Prompt evaluation page', href: '/prompt-evaluation' },
    { label: 'Templates', href: '/user-templates' },
    { label: 'Settings', href: '/settings' },
  ];
}
