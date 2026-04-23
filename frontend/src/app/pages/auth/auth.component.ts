import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.component.html',
  styleUrl: './auth.component.css'
})
export class AuthComponent {
  private api = inject(ApiService);
  private router = inject(Router);

  mode: 'login' | 'register' = 'login';
  loading = false;
  errorMessage = '';
  successMessage = '';

  loginData = { username: '', password: '' };
  registerData = { username: '', email: '', password: '' };

  switchMode(mode: 'login' | 'register') {
    this.mode = mode;
    this.errorMessage = '';
    this.successMessage = '';
  }

  onLogin() {
    if (!this.loginData.username || !this.loginData.password) {
      this.errorMessage = 'Please fill in all fields';
      return;
    }
    this.loading = true;
    this.errorMessage = '';

    this.api.login(this.loginData.username, this.loginData.password).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.loading = false;
        this.errorMessage = err.error?.detail || 'Invalid credentials';
      }
    });
  }

  onRegister() {
    if (!this.registerData.username || !this.registerData.email || !this.registerData.password) {
      this.errorMessage = 'Please fill in all fields';
      return;
    }
    this.loading = true;
    this.errorMessage = '';

    this.api.register(this.registerData.username, this.registerData.email, this.registerData.password).subscribe({
      next: () => {
        this.loading = false;
        this.successMessage = 'Account created! Logging in...';
        // Auto-login after register
        this.api.login(this.registerData.username, this.registerData.password).subscribe({
          next: () => this.router.navigate(['/']),
          error: () => {
            this.successMessage = '';
            this.mode = 'login';
          }
        });
      },
      error: (err) => {
        this.loading = false;
        const errors = err.error;
        if (errors?.username) this.errorMessage = errors.username[0];
        else if (errors?.email) this.errorMessage = errors.email[0];
        else if (errors?.password) this.errorMessage = errors.password[0];
        else this.errorMessage = 'Registration failed. Try again.';
      }
    });
  }
}
