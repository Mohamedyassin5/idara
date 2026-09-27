import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Auth } from '../core/auth.service';
import { I18n } from '../core/i18n';

@Component({
  imports: [FormsModule, RouterLink],
  template: `
    <section class="auth">
      <h1>{{ i18n.t(isRegister() ? 'register' : 'login') }}</h1>
      <p class="auth-sub">{{ i18n.t('authSub') }}</p>

      <form class="auth-form" (ngSubmit)="submit()">
        @if (isRegister()) {
          <label class="field">
            <span>{{ i18n.t('fullName') }}</span>
            <input name="name" [(ngModel)]="name" required autocomplete="name" />
          </label>
        }
        <label class="field">
          <span>{{ i18n.t('email') }}</span>
          <input name="email" type="email" [(ngModel)]="email" required autocomplete="email" />
        </label>
        <label class="field">
          <span>{{ i18n.t('password') }}</span>
          <input
            name="password"
            type="password"
            [(ngModel)]="password"
            required
            [minlength]="isRegister() ? 8 : 1"
            [autocomplete]="isRegister() ? 'new-password' : 'current-password'"
          />
          @if (isRegister()) {
            <small>{{ i18n.t('passwordHint') }}</small>
          }
        </label>

        @if (error()) {
          <p class="auth-error" role="alert">{{ error() }}</p>
        }

        <button class="btn primary big" type="submit" [disabled]="busy()">
          {{ i18n.t(isRegister() ? 'register' : 'login') }}
        </button>
      </form>

      <p class="auth-switch">
        {{ i18n.t(isRegister() ? 'haveAccount' : 'noAccount') }}
        <a [routerLink]="isRegister() ? '/login' : '/register'" [queryParams]="route.snapshot.queryParams">
          {{ i18n.t(isRegister() ? 'login' : 'register') }}
        </a>
      </p>
    </section>
  `,
})
export class AuthPage {
  protected readonly i18n = inject(I18n);
  protected readonly route = inject(ActivatedRoute);
  private readonly auth = inject(Auth);
  private readonly router = inject(Router);

  protected readonly isRegister = computed(() => this.route.snapshot.routeConfig?.path === 'register');
  protected name = '';
  protected email = '';
  protected password = '';
  protected readonly busy = signal(false);
  protected readonly error = signal('');

  protected async submit(): Promise<void> {
    if (this.busy()) return;
    this.error.set('');
    this.busy.set(true);
    try {
      if (this.isRegister()) await this.auth.register(this.name.trim(), this.email.trim(), this.password);
      else await this.auth.login(this.email.trim(), this.password);
      const returnUrl = this.route.snapshot.queryParamMap.get('returnUrl');
      await this.router.navigateByUrl(returnUrl?.startsWith('/') ? returnUrl : '/home');
    } catch (e) {
      const status = e instanceof HttpErrorResponse ? e.status : 0;
      this.error.set(
        status === 401
          ? this.i18n.t('authInvalid')
          : status === 409
            ? this.i18n.t('authExists')
            : status === 422
              ? this.i18n.t('authCheckFields')
              : this.i18n.t('errorBackend'),
      );
    } finally {
      this.busy.set(false);
    }
  }
}
