import { Component } from '@angular/core';
import { Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

@Component({
  selector: 'sd-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss'],
})
export class LoginComponent {
  email = '';
  password = '';
  errorMessage = '';
  isSubmitting = false;

  constructor(private readonly auth: AuthService, private readonly router: Router) {
    if (this.auth.isAuthenticated) void this.router.navigate(['/dashboard']);
  }

  submit(): void {
    if (this.isSubmitting) return;
    this.errorMessage = '';
    this.isSubmitting = true;
    this.auth.login(this.email.trim(), this.password).subscribe({
      next: (result) => {
        this.isSubmitting = false;
        if (!result.success) {
          this.errorMessage = result.message;
          return;
        }
        void this.router.navigate(['/dashboard']);
      },
      error: () => {
        this.isSubmitting = false;
        this.errorMessage = 'Could not connect to Society Doom. Check that the backend is running, then try again.';
      },
    });
  }
}
