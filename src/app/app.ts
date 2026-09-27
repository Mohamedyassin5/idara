import { Component, inject } from '@angular/core';
import { RouterLink, RouterOutlet } from '@angular/router';
import { Auth } from './core/auth.service';
import { I18n, LANGS } from './core/i18n';

@Component({
  imports: [RouterOutlet, RouterLink],
  selector: 'app-root',
  template: `
    <header class="topbar">
      <a class="brand" routerLink="/" [attr.aria-label]="i18n.t('back')">
        <svg class="brand-mark" viewBox="0 0 64 64" aria-hidden="true">
          <path d="M8 58V30a24 24 0 0 1 48 0v28z" fill="#fbf8f1" />
          <path d="M18 58V31a14 14 0 0 1 28 0v27z" fill="#c62828" />
          <circle cx="32" cy="8" r="3.5" fill="#b8631f" />
        </svg>
        <span class="brand-text">
          <strong>{{ i18n.t('appName') }}</strong>
          <small>{{ i18n.t('tagline') }}</small>
        </span>
      </a>
      <nav class="lang-switch" aria-label="Language">
        @for (l of langs; track l.code) {
          <button
            type="button"
            [class.active]="i18n.lang() === l.code"
            [attr.aria-pressed]="i18n.lang() === l.code"
            (click)="i18n.lang.set(l.code)"
          >
            {{ l.label }}
          </button>
        }
      </nav>
      <div class="user-menu">
        @if (auth.user(); as u) {
          <span class="user-name">{{ u.name }}</span>
          <button type="button" class="btn ghost small" (click)="auth.logout()">{{ i18n.t('logout') }}</button>
        } @else {
          <a class="btn ghost small" routerLink="/login">{{ i18n.t('login') }}</a>
          <a class="btn primary small" routerLink="/register">{{ i18n.t('register') }}</a>
        }
      </div>
    </header>

    <main><router-outlet /></main>

    <footer class="footer">
      <p>{{ i18n.t('footer') }}</p>
      <p class="made">✦ {{ i18n.t('madeIn') }}</p>
    </footer>
  `,
})
export class App {
  protected readonly i18n = inject(I18n);
  protected readonly auth = inject(Auth);
  protected readonly langs = LANGS;
}
