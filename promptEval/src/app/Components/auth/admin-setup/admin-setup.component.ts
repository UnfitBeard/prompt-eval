import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../Service/auth.service';

function matchPassword(group: AbstractControl): ValidationErrors | null {
  const pass = group.get('password')?.value ?? '';
  const confirm = group.get('confirmPassword')?.value ?? '';
  return pass && confirm && pass !== confirm ? { mismatch: true } : null;
}

@Component({
  selector: 'app-admin-setup',
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './admin-setup.component.html',
  styleUrl: './admin-setup.component.css',
})
export class AdminSetupComponent implements OnInit {
  form: FormGroup;
  submitted = false;
  loading = false;
  errorMsg = '';
  bootstrapEnabled = false;
  showPassword = false;
  currentYear = new Date().getFullYear();

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router
  ) {
    this.form = this.fb.group(
      {
        fullName: ['', [Validators.required, Validators.minLength(2)]],
        email: ['', [Validators.required, Validators.email]],
        password: ['', [Validators.required, Validators.minLength(8)]],
        confirmPassword: ['', [Validators.required]],
      },
      { validators: matchPassword }
    );
  }

  ngOnInit(): void {
    this.authService.getAdminBootstrapStatus().subscribe({
      next: (res) => {
        this.bootstrapEnabled = !!res?.enabled;
        if (!this.bootstrapEnabled) {
          this.router.navigate(['/login']);
        }
      },
      error: () => {
        this.bootstrapEnabled = false;
        this.router.navigate(['/login']);
      },
    });
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  onSubmit() {
    this.submitted = true;
    this.errorMsg = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const payload = this.form.getRawValue();
    this.loading = true;

    // 1) Create first admin (unauthenticated endpoint, but only works when no admins exist)
    // 2) Log in as that admin
    this.authService.bootstrapAdmin(payload).subscribe({
      next: () => {
        this.authService
          .login({ email: payload.email, password: payload.password })
          .subscribe({
            next: () => {
              this.loading = false;
              this.router.navigate(['admin/admin-dashboard']);
            },
            error: (err) => {
              this.loading = false;
              this.errorMsg =
                err?.error?.message ||
                err?.error?.detail ||
                err?.message ||
                'Admin created, but login failed. Please try logging in.';
            },
          });
      },
      error: (err) => {
        this.loading = false;
        this.errorMsg =
          err?.error?.message ||
          err?.error?.detail ||
          err?.message ||
          'Admin setup failed.';
      },
    });
  }
}
