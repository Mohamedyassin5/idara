import { HttpClient } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { toString as qrToString } from 'qrcode';
import { I18n } from '../core/i18n';

/** Slash command that selects each agent in the WhatsApp bot (see docs/whatsapp.md). */
const COMMAND: Record<string, string> = {
  'bureaucratie-agent': 'bureaucratie',
  'steg-agent': 'steg',
  'entrepreneuriat-agent': 'entrepreneuriat',
  'louage-agent': 'louage',
  'parking-agent': 'parking',
  'souk-agent': 'souk',
  'bac-agent': 'bac',
  'job-agent': 'job',
  'immobilier-agent': 'immobilier',
};

/** QR code (and button, for phones) that opens a WhatsApp chat with the bot, the agent command already typed. */
@Component({
  selector: 'app-whatsapp-card',
  template: `
    @if (link(); as href) {
      <section class="wa" aria-labelledby="wa-title">
        @if (qr(); as svg) {
          <div class="wa-qr" [innerHTML]="svg" role="img" [attr.aria-label]="i18n.t('waTitle')"></div>
        }
        <div class="wa-text">
          <h2 id="wa-title">{{ i18n.t('waTitle') }}</h2>
          <p>{{ i18n.t('waSub') }}</p>
          <a class="btn primary" [href]="href" target="_blank" rel="noopener">{{ i18n.t('waOpen') }}</a>
        </div>
      </section>
    }
  `,
  styles: `
    .wa {
      display: flex;
      align-items: center;
      gap: 1.2rem;
      flex-wrap: wrap;
      padding: 1rem 1.2rem;
      background: var(--glass);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    /* QR codes need a light background and a quiet zone to scan reliably, whatever the theme. */
    .wa-qr {
      flex: 0 0 auto;
      width: 132px;
      height: 132px;
      padding: 8px;
      background: #fff;
      border-radius: 12px;
    }

    .wa-qr ::ng-deep svg {
      display: block;
      width: 100%;
      height: 100%;
    }

    .wa-text { flex: 1 1 220px; min-width: 0; }
    .wa-text h2 { margin: 0 0 0.3rem; font-size: 1.05rem; }
    .wa-text p { margin: 0 0 0.7rem; color: var(--muted); font-size: 0.9rem; }
  `,
})
export class WhatsappCard {
  /** Backend id of the agent the page belongs to; empty for the free assistant (opens the menu). */
  readonly agentId = input<string>('');

  protected readonly i18n = inject(I18n);
  private readonly http = inject(HttpClient);

  private readonly number = signal('');
  protected readonly qr = signal('');

  protected readonly link = computed(() => {
    const number = this.number();
    if (!number) return '';
    const command = COMMAND[this.agentId()];
    return `https://wa.me/${number}?text=${encodeURIComponent(command ? `/${command}` : '/menu')}`;
  });

  constructor() {
    this.http.get<{ number: string }>('/api/whatsapp/info').subscribe({
      next: (res) => this.number.set(res.number),
      error: () => this.number.set(''), // WhatsApp not configured: the card stays hidden
    });
    // Regenerates the code whenever the link changes (the number arriving, or another agent page).
    effect(() => {
      const href = this.link();
      if (!href) {
        this.qr.set('');
        return;
      }
      qrToString(href, { type: 'svg', margin: 0, errorCorrectionLevel: 'M', color: { dark: '#000000', light: '#ffffff' } }).then(
        (svg) => this.qr.set(svg),
      );
    });
  }
}
