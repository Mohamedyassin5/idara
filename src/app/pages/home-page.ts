import { Component, computed, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AGENTS, HUBS, agentsOfHub } from '../core/agents';
import { I18n } from '../core/i18n';
import { Icon } from '../core/icon';
import { Marquee } from '../core/marquee';

const TYPE_MS = 42;
const ERASE_MS = 18;
const HOLD_MS = 1900;

@Component({
  imports: [FormsModule, RouterLink, Icon, Marquee],
  template: `
    <section class="hero">
      <div class="hero-grid">
        <div class="hero-copy">
          <p class="eyebrow">{{ i18n.t('appName') }} · ✦</p>
          <h1>{{ i18n.t('heroTitle') }}</h1>
          <p class="lead">{{ i18n.t('heroSub') }}</p>
          <form class="ask-bar" (ngSubmit)="ask()">
            <input
              name="q"
              [(ngModel)]="question"
              [placeholder]="typed() || i18n.t('askAnything')"
              [attr.aria-label]="i18n.t('askAnything')"
              autocomplete="off"
            />
            <button type="submit" class="btn primary">
              {{ i18n.t('askAssistant') }} <app-icon name="arrow" class="flip-rtl" />
            </button>
          </form>
        </div>

        <!-- Orbit: the real architecture. Centre = orchestrator, inner ring = 4 hubs, outer ring = 11 agents. -->
        <figure class="orbit-arch" aria-label="{{ caption() }}">
          <div class="orbit-stage" aria-hidden="true">
            <div class="ring ring-outer" style="--dur: 90s; --dir: normal; --inv: reverse">
              @for (agent of agents; track agent.slug; let i = $index) {
                <a
                  class="orb"
                  [routerLink]="['/agent', agent.slug]"
                  tabindex="-1"
                  [style.--i]="i"
                  [style.--n]="agents.length"
                  [style.--accent]="agent.accent"
                >
                  <span class="orb-counter">
                    <span class="orb-face"><app-icon [name]="agent.icon" /></span>
                    <span class="orb-tip">{{ i18n.pick(agent.name) }}</span>
                  </span>
                </a>
              }
            </div>
            <div class="ring ring-inner" style="--dur: 60s; --dir: reverse; --inv: normal">
              @for (hub of hubs; track hub.id; let i = $index) {
                <span class="orb hub-orb" [style.--i]="i" [style.--n]="hubs.length" [style.--accent]="hub.accent">
                  <span class="orb-counter">
                    <span class="orb-face"><app-icon [name]="hub.icon" /></span>
                    <span class="orb-tip">{{ i18n.pick(hub.name) }}</span>
                  </span>
                </span>
              }
            </div>
            <a class="orbit-core" routerLink="/assistant" tabindex="-1">
              <app-icon name="compass" />
            </a>
          </div>
          <figcaption>{{ caption() }}</figcaption>
        </figure>
      </div>
    </section>

    <section class="container">
      <h2 class="section-title reveal">{{ i18n.t('domains') }}</h2>
      <div class="marquee reveal" appMarquee>
        <div class="marquee-track">
          @for (copy of copies; track copy) {
            @for (agent of agents; track agent.slug) {
              <a
                class="agent-card"
                [routerLink]="['/agent', agent.slug]"
                [style.--accent]="agent.accent"
                [attr.aria-hidden]="copy ? true : null"
                [attr.tabindex]="copy ? -1 : null"
              >
                <span class="agent-icon" aria-hidden="true"><app-icon [name]="agent.icon" /></span>
                <span class="agent-name">{{ i18n.pick(agent.name) }}</span>
                <span class="agent-desc">{{ i18n.pick(agent.description) }}</span>
                <span class="agent-go" aria-hidden="true"><app-icon name="arrow" class="flip-rtl" /></span>
                @if (!agent.ready) {
                  <span class="chip soon">{{ i18n.t('soon') }}</span>
                }
              </a>
            }
          }
        </div>
      </div>
    </section>
  `,
})
export class HomePage {
  protected readonly i18n = inject(I18n);
  private readonly router = inject(Router);
  protected readonly hubs = HUBS;
  protected readonly agents = AGENTS;
  protected readonly agentsOf = agentsOfHub;
  /** Cards are rendered twice so the marquee loops seamlessly. */
  protected readonly copies = [0, 1];
  protected readonly question = signal('');

  /** Text currently "typed" in the search bar placeholder. */
  protected readonly typed = signal('');

  protected readonly caption = computed(() =>
    this.i18n
      .t('orbitCaption')
      .replace('{h}', String(HUBS.length))
      .replace('{a}', String(AGENTS.length)),
  );

  constructor() {
    // Typewriter placeholder cycling through one sample question per agent, in the current language.
    effect((onCleanup) => {
      const prompts = AGENTS.filter((a) => a.ready).map((a) => this.i18n.pick(a.prompts[0]));
      const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
      if (reduced) {
        this.typed.set('');
        return;
      }

      let timer: ReturnType<typeof setTimeout>;
      let idx = 0;
      let pos = 0;
      let erasing = false;

      const tick = () => {
        const full = prompts[idx];
        if (!erasing) {
          pos++;
          this.typed.set(full.slice(0, pos));
          if (pos >= full.length) {
            erasing = true;
            timer = setTimeout(tick, HOLD_MS);
            return;
          }
          timer = setTimeout(tick, TYPE_MS);
        } else {
          pos--;
          this.typed.set(full.slice(0, pos));
          if (pos <= 0) {
            erasing = false;
            idx = (idx + 1) % prompts.length;
            timer = setTimeout(tick, 350);
            return;
          }
          timer = setTimeout(tick, ERASE_MS);
        }
      };

      this.typed.set('');
      timer = setTimeout(tick, 600);
      onCleanup(() => clearTimeout(timer));
    });
  }

  protected ask(): void {
    const q = this.question().trim();
    this.router.navigate(['/assistant'], q ? { queryParams: { q } } : {});
  }
}
