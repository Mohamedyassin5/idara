import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18n, UiKey } from '../core/i18n';
import { WhatsappCard } from '../shared/whatsapp-card';

@Component({
  imports: [RouterLink, WhatsappCard],
  template: `
    <section class="landing-hero">
      <p class="landing-eyebrow">✦ {{ i18n.t('appName') }} ✦</p>
      <h1 class="landing-slogan">{{ i18n.t('landingSlogan') }}</h1>
      <p class="landing-sub">{{ i18n.t('landingSub') }}</p>
      <div class="landing-cta">
        <a class="btn primary big" routerLink="/home">{{ i18n.t('landingStart') }}</a>
        <a class="btn ghost big" routerLink="/assistant">{{ i18n.t('landingAsk') }}</a>
      </div>
    </section>

    <section class="landing-whatsapp">
      <app-whatsapp-card />
    </section>

    <section class="landing-features">
      <h2>{{ i18n.t('landingWhy') }}</h2>
      <div class="landing-grid">
        @for (f of features; track f.n) {
          <article>
            <span class="landing-num">{{ f.n }}</span>
            <h3>{{ i18n.t(f.title) }}</h3>
            <p>{{ i18n.t(f.desc) }}</p>
          </article>
        }
      </div>
    </section>

    <section class="landing-closing">
      <h2>{{ i18n.t('landingClosing') }}</h2>
      <a class="btn primary big" routerLink="/home">{{ i18n.t('landingStart') }}</a>
    </section>
  `,
})
export class LandingPage {
  protected readonly i18n = inject(I18n);
  protected readonly features: { n: string; title: UiKey; desc: UiKey }[] = [
    { n: 'I', title: 'landingF1t', desc: 'landingF1d' },
    { n: 'II', title: 'landingF2t', desc: 'landingF2d' },
    { n: 'III', title: 'landingF3t', desc: 'landingF3d' },
    { n: 'IV', title: 'landingF4t', desc: 'landingF4d' },
  ];
}
