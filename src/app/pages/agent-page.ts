import { Component, computed, effect, inject, input, signal, untracked, viewChild, ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { marked } from 'marked';
import { AgentConfig, AgentForm, FormField, HUBS, agentBySlug, agentByBackendId } from '../core/agents';
import { ChatError, ChatMessage, ChatService } from '../core/chat.service';
import { I18n } from '../core/i18n';
import { Icon } from '../core/icon';

const TUNIS_CENTRE = { lat: '36.8002', lng: '10.1815' };

/** Pseudo-agent used by /assistant: no domain hint, the orchestrator routes freely. */
const ASSISTANT: AgentConfig = {
  slug: 'assistant',
  backendId: '',
  hubId: '',
  icon: 'compass',
  accent: '#1f5fa8',
  ready: true,
  name: { fr: 'Assistant Idara', ar: 'مساعد إدارة', en: 'Idara assistant' },
  description: {
    fr: 'Posez votre question : l’orchestrateur choisit automatiquement le bon domaine.',
    ar: 'اطرح سؤالك: يختار المنسّق تلقائيا المجال المناسب.',
    en: 'Ask your question: the orchestrator automatically picks the right domain.',
  },
  prompts: [
    {
      fr: 'Quels papiers faut-il pour renouveler ma carte d’identité ?',
      ar: 'شنوة الوثائق المطلوبة لتجديد بطاقة التعريف؟',
      en: 'Which documents do I need to renew my ID card?',
    },
    {
      fr: 'Comment payer ma facture STEG en ligne ?',
      ar: 'كيفاش نخلّص فاتورة الستاغ أونلاين؟',
      en: 'How can I pay my STEG bill online?',
    },
    {
      fr: 'Y a-t-il un louage de Tunis à Sousse ce soir ?',
      ar: 'فما لواج من تونس لسوسة الليلة؟',
      en: 'Is there a louage from Tunis to Sousse tonight?',
    },
  ],
};

@Component({
  imports: [FormsModule, RouterLink, Icon],
  template: `
    @if (agent(); as a) {
      <div class="agent-page" [style.--accent]="a.accent">
        <section class="agent-hero">
          <div class="container narrow">
            <a class="back" routerLink="/home">← {{ i18n.t('back') }}</a>
            <div class="agent-title">
              <span class="agent-icon lg" aria-hidden="true"><app-icon [name]="a.icon" /></span>
              <div>
                <h1>{{ i18n.pick(a.name) }}</h1>
                <p>{{ i18n.pick(a.description) }}</p>
                @if (hubName(); as hn) {
                  <span class="chip">{{ hn }}</span>
                }
                @if (!a.ready) {
                  <span class="chip soon">{{ i18n.t('soon') }}</span>
                }
              </div>
            </div>
            @if (!a.ready) {
              <p class="notice">{{ i18n.t('soonNote') }}</p>
            }
          </div>
        </section>

        <div class="container narrow chat">
          @if (a.form; as form) {
            <details class="quick-form" open>
              <summary>{{ i18n.pick(form.title) }}</summary>
              <form (ngSubmit)="submitForm(form)">
                @for (f of form.fields; track f.key) {
                  @if (f.type === 'geo') {
                    <div class="field geo">
                      <label>{{ i18n.pick(f.label) }}</label>
                      <div class="geo-row">
                        <input type="text" inputmode="decimal" name="lat" placeholder="lat" [ngModel]="lat()" (ngModelChange)="lat.set($event)" aria-label="latitude" />
                        <input type="text" inputmode="decimal" name="lng" placeholder="lng" [ngModel]="lng()" (ngModelChange)="lng.set($event)" aria-label="longitude" />
                        <button type="button" class="btn ghost" (click)="locate()" [disabled]="locating()">
                          <app-icon name="locate" /> {{ locating() ? i18n.t('locating') : i18n.t('myLocation') }}
                        </button>
                      </div>
                      @if (geoError()) {
                        <small class="hint-error">{{ i18n.t('locationDenied') }}</small>
                      }
                    </div>
                  } @else if (f.type === 'select') {
                    <div class="field">
                      <label [attr.for]="'f-' + f.key">{{ i18n.pick(f.label) }}</label>
                      <select [id]="'f-' + f.key" [name]="f.key" [ngModel]="selectValue(f)" (ngModelChange)="setValue(f.key, $event)">
                        @for (o of f.options ?? []; track o.fr) {
                          <option [value]="i18n.pick(o)">{{ i18n.pick(o) }}</option>
                        }
                      </select>
                    </div>
                  } @else {
                    <div class="field">
                      <label [attr.for]="'f-' + f.key">{{ i18n.pick(f.label) }}</label>
                      <input
                        [id]="'f-' + f.key"
                        [name]="f.key"
                        type="text"
                        [placeholder]="f.placeholder ? i18n.pick(f.placeholder) : ''"
                        [ngModel]="values()[f.key] ?? ''"
                        (ngModelChange)="setValue(f.key, $event)"
                      />
                    </div>
                  }
                }
                <button type="submit" class="btn primary" [disabled]="loading() || !formReady(form)">
                  {{ i18n.t('ask') }}
                </button>
              </form>
            </details>
          }

          @if (messages().length === 0) {
            <div class="suggestions">
              <h2>{{ i18n.t('suggestions') }}</h2>
              <div class="chips">
                @for (p of a.prompts; track p.fr) {
                  <button type="button" class="chip action" (click)="send(i18n.pick(p))" [disabled]="loading()">
                    {{ i18n.pick(p) }}
                  </button>
                }
              </div>
            </div>
          }

          <ol class="messages" aria-live="polite">
            @for (m of messages(); track $index) {
              <li class="msg" [class.user]="m.role === 'user'" [class.error]="m.role === 'error'">
                @if (m.role === 'user') {
                  <span class="who">{{ i18n.t('you') }}</span>
                  <p>{{ m.text }}</p>
                } @else if (m.role === 'error') {
                  <p>{{ m.text }}</p>
                } @else {
                  <span class="who"><app-icon [name]="a.icon" /> {{ i18n.t('assistantName') }}</span>
                  <div class="md" [innerHTML]="render(m.text)"></div>
                  @if (answeredBy(m); as by) {
                    <p class="by">{{ i18n.t('answeredBy') }} <strong>{{ by }}</strong></p>
                  }
                  @if (wrongAgent(m)) {
                    <p class="by warn">{{ i18n.t('routedElsewhere') }}</p>
                  }
                }
              </li>
            }
            @if (loading()) {
              <li class="msg thinking"><span class="dots" aria-hidden="true"><i></i><i></i><i></i></span> {{ i18n.t('thinking') }}</li>
            }
          </ol>
          <div #bottom></div>
        </div>

        <form class="composer" (ngSubmit)="send(draft())">
          <div class="container narrow composer-row">
            @if (messages().length) {
              <button type="button" class="btn ghost" (click)="reset()">{{ i18n.t('newChat') }}</button>
            }
            <input
              name="draft"
              [ngModel]="draft()"
              (ngModelChange)="draft.set($event)"
              [placeholder]="i18n.t('placeholder')"
              [attr.aria-label]="i18n.t('placeholder')"
              autocomplete="off"
            />
            <button type="submit" class="btn primary" [disabled]="loading() || !draft().trim()"><app-icon name="send" /> {{ i18n.t('send') }}</button>
          </div>
        </form>
      </div>
    } @else {
      <div class="container narrow not-found">
        <h1>404</h1>
        <p>{{ i18n.t('notFound') }}</p>
        <a class="btn primary" routerLink="/home">{{ i18n.t('back') }}</a>
      </div>
    }
  `,
})
export class AgentPage {
  protected readonly i18n = inject(I18n);
  private readonly chat = inject(ChatService);

  // Bound from the route (withComponentInputBinding): /agent/:slug, route data, ?q=
  readonly slug = input<string>();
  readonly assistant = input<boolean>(false);
  readonly q = input<string>();

  private readonly bottom = viewChild<ElementRef<HTMLElement>>('bottom');

  protected readonly agent = computed(() => (this.assistant() ? ASSISTANT : agentBySlug(this.slug() ?? '')));
  private readonly key = computed(() => (this.assistant() ? 'assistant' : (this.slug() ?? '')));
  private readonly conv = computed(() => this.chat.conversation(this.key()));
  protected readonly messages = computed(() => this.conv().messages());

  protected readonly hubName = computed(() => {
    const hub = HUBS.find((h) => h.id === this.agent()?.hubId);
    return hub ? this.i18n.pick(hub.name) : '';
  });

  protected readonly loading = signal(false);
  protected readonly draft = signal('');
  protected readonly values = signal<Record<string, string>>({});
  protected readonly lat = signal(TUNIS_CENTRE.lat); // default: Tunis centre, so the form works without geolocation
  protected readonly lng = signal(TUNIS_CENTRE.lng);
  protected readonly locating = signal(false);
  protected readonly geoError = signal(false);

  private autoAsked = false;

  constructor() {
    // Scroll to the newest message.
    effect(() => {
      this.messages();
      this.loading();
      const el = this.bottom()?.nativeElement;
      if (el) setTimeout(() => el.scrollIntoView({ behavior: 'smooth', block: 'end' }));
    });
    // /assistant?q=… (from the home page): send the question once.
    effect(() => {
      const q = this.q()?.trim();
      if (q && this.assistant() && !this.autoAsked) {
        this.autoAsked = true;
        untracked(() => this.send(q));
      }
    });
  }

  protected render(text: string): string {
    return marked.parse(text, { async: false, breaks: true }) as string; // sanitized by Angular in [innerHTML]
  }

  protected answeredBy(m: ChatMessage): string {
    const found = m.agentId ? agentByBackendId(m.agentId) : undefined;
    return found ? this.i18n.pick(found.name) : '';
  }

  protected wrongAgent(m: ChatMessage): boolean {
    const a = this.agent();
    return !!a && !this.assistant() && !!m.agentId && m.agentId !== a.backendId;
  }

  protected send(text: string): void {
    const question = text.trim();
    const a = this.agent();
    if (!question || !a || this.loading()) return;

    const conv = this.conv();
    conv.messages.update((list) => [...list, { role: 'user', text: question }]);
    this.draft.set('');
    this.loading.set(true);

    this.chat.ask(this.withDomainHint(a, question), conv.session).subscribe({
      next: (ans) => {
        conv.messages.update((list) => [...list, { role: 'assistant', text: ans.content, agentId: ans.agentId }]);
        this.loading.set(false);
      },
      error: (err: unknown) => {
        const kind = err instanceof ChatError ? err.kind : 'generic';
        conv.messages.update((list) => [
          ...list,
          { role: 'error', text: this.i18n.t(kind === 'backend' ? 'errorBackend' : 'errorGeneric') },
        ]);
        this.loading.set(false);
      },
    });
  }

  protected reset(): void {
    this.chat.reset(this.key());
  }

  // ---- quick form -------------------------------------------------------------------------------

  protected selectValue(f: FormField): string {
    const current = this.values()[f.key];
    if (current !== undefined) return current;
    const first = f.options?.[0];
    return first ? this.i18n.pick(first) : '';
  }

  protected setValue(key: string, value: string): void {
    this.values.update((v) => ({ ...v, [key]: value }));
  }

  protected formReady(form: AgentForm): boolean {
    return form.fields.every((f) => {
      if (f.type === 'geo') return this.isCoordinate(this.lat()) && this.isCoordinate(this.lng());
      if (f.type === 'select') return true;
      return (this.values()[f.key] ?? '').trim().length > 0;
    });
  }

  protected submitForm(form: AgentForm): void {
    if (!this.formReady(form)) return;
    const data: Record<string, string> = { lat: this.lat().trim(), lng: this.lng().trim() };
    for (const f of form.fields) {
      if (f.type === 'select') data[f.key] = this.selectValue(f);
      else if (f.type === 'text') data[f.key] = (this.values()[f.key] ?? '').trim();
    }
    const question = this.i18n.pick(form.template).replace(/\{(\w+)\}/g, (_, k: string) => data[k] ?? '');
    this.send(question);
  }

  protected locate(): void {
    if (!navigator.geolocation) {
      this.geoError.set(true);
      return;
    }
    this.geoError.set(false);
    this.locating.set(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        this.lat.set(pos.coords.latitude.toFixed(5));
        this.lng.set(pos.coords.longitude.toFixed(5));
        this.locating.set(false);
      },
      () => {
        this.geoError.set(true);
        this.locating.set(false);
      },
      { timeout: 8000 },
    );
  }

  private isCoordinate(v: string): boolean {
    return v.trim() !== '' && Number.isFinite(Number(v));
  }

  /**
   * Only the Master Orchestrator is exposed by the backend, so a domain page cannot call its agent directly.
   * A short bracketed hint nudges the routing toward this page's domain; the user's visible message stays clean.
   */
  private withDomainHint(a: AgentConfig, question: string): string {
    return a.slug === 'assistant' ? question : `[Domaine : ${a.name.fr}] ${question}`;
  }
}
