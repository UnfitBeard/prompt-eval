import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import {
  FormBuilder,
  FormGroup,
  FormsModule,
  ReactiveFormsModule,
  Validators,
} from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-login',
  imports: [CommonModule, ReactiveFormsModule, FormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  form: FormGroup;
  showPassword = false;
  currentYear = new Date().getFullYear();

  constructor(private fb: FormBuilder) {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
    });
  }

  togglePassword() {
    this.showPassword = !this.showPassword;
  }

  forgotPassword() {
    console.log('Forgot password clicked');
    // route to /forgot-password or open modal
  }

  onSubmit() {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }
    console.log('SIGN IN →', this.form.value);
    // call auth service here
  }

  social(provider: 'google' | 'github') {
    console.log('SOCIAL SIGN-IN →', provider);
  }

  // convenience getters for template errors
  get email() {
    return this.form.get('email');
  }
  get password() {
    return this.form.get('password');
  }
}
