import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../Service/auth.service';
import { UserRole } from '../../../models/course.model';

@Component({
  selector: 'app-login',
  imports: [CommonModule, ReactiveFormsModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent implements OnInit {
  form: FormGroup;
  showPassword = false;
  currentYear = new Date().getFullYear();
  loading = false;
  errorMsg = '';
  adminBootstrapEnabled = false;

  ngOnInit(): void {
    // If no admins exist yet, the backend allows a one-time bootstrap.
    this.authService.getAdminBootstrapStatus().subscribe({
      next: (res) => {
        this.adminBootstrapEnabled = !!res?.enabled;
      },
      error: () => {
        // If the check fails, simply hide the link.
        this.adminBootstrapEnabled = false;
      },
    });
  }

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required /*Validators.minLength(8)*/]],
    });
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  forgotPassword() {
    console.log('Forgot password clicked');
    // route to /forgot-password or open modal
  }

  // convenience getters for template errors
  get email() {
    return this.form.get('email');
  }
  get password() {
    return this.form.get('password');
  }
  onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.errorMsg = '';
    this.loading = true;
    console.log('SIGN IN →', this.form.value);
    // call auth service here
    this.authService
      .login({ email: this.email?.value, password: this.password?.value })
      .subscribe({
        next: (token) => {
          const role = token?.user?.role;
          if (role === UserRole.ADMIN) {
            this.router.navigate(['admin/admin-dashboard']);
          } else {
            this.router.navigate(['dashboard']);
          }
        },
        error: (err) => {
          this.errorMsg =
            err?.error?.message ||
            err?.error?.detail ||
            err?.message ||
            'Login failed. Please try again';
          console.error(this.errorMsg);
        },
      });
  }

  social(provider: 'google' | 'github') {
    console.log('SOCIAL SIGN-IN →', provider);
  }
}
