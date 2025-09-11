import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import {
  AbstractControl,
  Form,
  FormBuilder,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';

function matchPassword(group: AbstractControl): ValidationErrors | null {
  const pass = group.get('password')?.value ?? '';
  const confirm = group.get('confirmPassword')?.value ?? '';
  return pass && confirm && pass !== confirm ? { mismatch: true } : null;
}

@Component({
  selector: 'app-registration',
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './registration.component.html',
  styleUrl: './registration.component.css',
})
export class RegistrationComponent {
  form: FormGroup;
  show = { password: false, confirm: false };

  constructor(private fb: FormBuilder) {
    this.form = this.fb.group(
      {
        fullName: ['', [Validators.required, Validators.minLength(2)]],
        email: ['', [Validators.required, Validators.email]],
        password: [
          '',
          [
            Validators.required,
            Validators.minLength(8),
            // at least 3 of: lower, upper, number, symbol (soft check via pattern sets)
          ],
        ],
        confirmPassword: ['', [Validators.required]],
        organization: [''],
        agree: [true],
      },
      { validators: matchPassword }
    );
  }

  // -------- Password strength (0..100) + label/color ----------
  get pwd(): string {
    return this.form.get('password')?.value || '';
  }

  get strengthScore(): number {
    const p = this.pwd;
    if (!p) return 0;
    let score = 0;
    const rules = [
      /.{8,}/, // length >= 8
      /[a-z]/, // lowercase
      /[A-Z]/, // uppercase
      /[0-9]/, // number
      /[^A-Za-z0-9]/, // symbol
      /.{12,}/, // bonus for 12+
    ];
    rules.forEach((r) => {
      if (r.test(p)) score += 1;
    });
    return Math.min(100, Math.round((score / rules.length) * 100));
  }
  get strengthLabel(): string {
    const s = this.strengthScore;
    if (s >= 80) return 'Strong password';
    if (s >= 50) return 'Medium password';
    return 'Weak password';
  }
  get strengthBarClass(): string {
    const s = this.strengthScore;
    if (s >= 80) return 'bg-emerald-500';
    if (s >= 50) return 'bg-amber-500';
    return 'bg-red-500';
  }

  // -------- Helpers ----------
  toggle(which: 'password' | 'confirm') {
    this.show[which] = !this.show[which];
  }

  hasError(name: string, err: string): boolean {
    const c = this.form.get(name);
    return !!(c && (c.touched || this.submitted) && c.errors?.[err]);
  }

  submitted = false;
  onSubmit() {
    this.submitted = true;
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    const { fullName, email, password, organization } = this.form.value;
    const payload = { fullName, email, password, organization };
    console.log('REGISTER →', payload);
    alert('Account created (demo)! Check console for payload.');
  }

  social(provider: 'google' | 'github' | 'sso') {
    console.log('SOCIAL SIGNUP →', provider);
  }
}
