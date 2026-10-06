import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, inject, input, signal } from '@angular/core';
import { finalize } from 'rxjs';
import { GeoPayload } from '../core/chat.service';
import { GeoResult } from './geo-result';

export interface CvAnalysis {
  headline: string;
  score: number;
  strengths: string[];
  gaps: string[];
  skills: { name: string; level: string }[];
  experiences: { title: string; organization: string; period: string; highlights: string[] }[];
  suggested_roles: { title: string; why: string; match_percent: number }[];
  next_steps: string[];
}

const ACCEPTED = ['.pdf', '.txt', '.md'];

/** Upload a CV, get a card-based analysis back. Nothing here is a chat: one drop zone, one result board. */
@Component({
  selector: 'app-cv-workspace',
  imports: [GeoResult],
  template: `
    <section class="cv" [style.--accent]="accent()">
      <label
        class="drop"
        [class.busy]="loading()"
        (dragover)="$event.preventDefault()"
        (drop)="onDrop($event)"
      >
        <input type="file" [accept]="accepted" (change)="onPick($event)" [disabled]="loading()" />
        <span class="drop-ico" aria-hidden="true">⤒</span>
        <strong>{{ loading() ? 'Analyse de votre CV…' : 'Déposez votre CV ici' }}</strong>
        <span class="hint">PDF, TXT ou MD · 5 Mo maximum · ou cliquez pour choisir</span>
      </label>

      @if (error()) {
        <p class="err" role="alert">{{ error() }}</p>
      }

      @if (analysis(); as a) {
        <div class="board">
          <article class="card hero">
            <div class="ring" [style.--pct]="a.score" aria-label="Score du CV {{ a.score }} sur 100">
              <span>{{ a.score }}</span>
            </div>
            <div>
              <span class="tag">Qualité du CV</span>
              <p class="headline">{{ a.headline }}</p>
            </div>
          </article>

          <article class="card">
            <h3>Points forts</h3>
            <ul class="check">
              @for (s of a.strengths; track $index) { <li>{{ s }}</li> }
            </ul>
          </article>

          <article class="card">
            <h3>À améliorer</h3>
            <ul class="cross">
              @for (g of a.gaps; track $index) { <li>{{ g }}</li> }
            </ul>
          </article>

          <article class="card wide">
            <h3>Compétences relevées</h3>
            <div class="chips">
              @for (s of a.skills; track $index) {
                <span class="chip"
                  >{{ s.name }} <small>{{ s.level }}</small></span
                >
              }
            </div>
          </article>

          <article class="card wide">
            <h3>Pistes de poste</h3>
            @for (r of a.suggested_roles; track $index) {
              <div class="role">
                <div class="role-top">
                  <strong>{{ r.title }}</strong>
                  <span class="pct">{{ r.match_percent }}%</span>
                </div>
                <div class="bar"><i [style.width.%]="r.match_percent"></i></div>
                <p>{{ r.why }}</p>
                <button type="button" class="offers-btn" (click)="loadOffers(r.title)" [disabled]="offersLoading()[r.title]">
                  {{ offersLoading()[r.title] ? 'Recherche…' : 'Voir les offres' }}
                </button>
                @if (offerError()[r.title]; as msg) { <p class="err-inline">{{ msg }}</p> }
                @if (offers()[r.title]; as payload) {
                  @if (payload.items.length === 0) {
                    <p class="err-inline">Aucune offre trouvée pour ce poste pour le moment.</p>
                  } @else {
                    <ul class="offer-list">
                      @for (o of payload.items; track $index) {
                        <li class="offer">
                          <div class="offer-main">
                            <strong>{{ o['name'] }}</strong>
                            <span class="offer-co">{{ o['company'] }}@if (o['address']) { · {{ o['address'] }}}</span>
                          </div>
                          <div class="offer-side">
                            <span class="tag" [class.stage]="o['category'] === 'stage'">{{ o['category'] }}</span>
                            @if (o['url']) { <a [href]="o['url']" target="_blank" rel="noopener">Postuler →</a> }
                          </div>
                        </li>
                      }
                    </ul>
                    @if (hasCoords(payload)) {
                      <app-geo-result [payload]="payload" [accent]="accent()" />
                    }
                  }
                }
              </div>
            }
          </article>

          <article class="card">
            <h3>Prochaines étapes</h3>
            <ol class="steps">
              @for (n of a.next_steps; track $index) { <li>{{ n }}</li> }
            </ol>
          </article>

          @if (a.experiences.length) {
            <article class="card wide">
              <h3>Expériences</h3>
              <div class="exp-grid">
                @for (e of a.experiences; track $index) {
                  <div class="exp">
                    <strong>{{ e.title }}</strong>
                    <span class="meta">{{ e.organization }}@if (e.period) { · {{ e.period }}}</span>
                    <ul>
                      @for (h of e.highlights; track $index) { <li>{{ h }}</li> }
                    </ul>
                  </div>
                }
              </div>
            </article>
          }
        </div>
      }
    </section>
  `,
  styles: `
    :host { display: block; }

    .cv { display: flex; flex-direction: column; gap: 1rem; }

    .drop {
      position: relative;
      display: grid;
      place-items: center;
      gap: 0.25rem;
      padding: 1.6rem 1rem;
      text-align: center;
      background: color-mix(in srgb, var(--accent) 5%, transparent);
      border: 2px dashed color-mix(in srgb, var(--accent) 45%, transparent);
      border-radius: var(--radius);
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;
    }

    .drop:hover { background: color-mix(in srgb, var(--accent) 10%, transparent); }
    .drop.busy { cursor: progress; opacity: 0.75; }
    .drop input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
    .drop input:disabled { cursor: progress; }
    .drop-ico { font-size: 1.8rem; color: var(--accent); line-height: 1; }
    .hint { font-size: 0.82rem; color: var(--muted); }

    .err { margin: 0; color: #ffc9c6; background: rgb(240 96 90 / 14%); border: 1px solid rgb(240 96 90 / 35%); border-radius: 10px; padding: 0.6rem 0.8rem; }

    .board {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 0.8rem;
    }

    .card {
      background: var(--glass);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
      border: 1px solid var(--glass-border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 0.95rem 1.05rem;
      min-width: 0;
    }

    .card.wide { grid-column: 1 / -1; }

    .card h3 {
      margin: 0 0 0.5rem;
      font-size: 0.9rem;
      color: var(--accent);
    }

    .card.hero {
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      gap: 1.1rem;
      background: color-mix(in srgb, var(--accent) 7%, transparent);
    }

    .headline { margin: 0.2rem 0 0; font-size: 1.05rem; font-weight: 600; }
    .tag { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }

    .ring {
      --pct: 0;
      flex: 0 0 auto;
      width: 84px;
      height: 84px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      background: conic-gradient(var(--accent) calc(var(--pct) * 1%), var(--line) 0);
    }

    .ring span {
      display: grid;
      place-items: center;
      width: 68px;
      height: 68px;
      border-radius: 50%;
      background: var(--bg-elev);
      font-weight: 700;
      font-size: 1.2rem;
      color: var(--accent);
    }

    ul { margin: 0; padding-inline-start: 1.1rem; }
    li { margin-block: 0.25rem; }
    ul.check li::marker { color: var(--green); }
    ul.cross li::marker { color: var(--red); }

    .steps { padding-inline-start: 1.3rem; }
    .steps li::marker { color: var(--accent); font-weight: 700; }

    .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .chip {
      display: inline-flex;
      align-items: baseline;
      gap: 0.35rem;
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      background: color-mix(in srgb, var(--accent) 10%, transparent);
      border: 1px solid color-mix(in srgb, var(--accent) 25%, transparent);
      font-size: 0.85rem;
    }
    .chip small { color: var(--muted); font-size: 0.72rem; }

    .role { margin-block-end: 0.8rem; }
    .role:last-child { margin-block-end: 0; }
    .role-top { display: flex; justify-content: space-between; align-items: baseline; gap: 0.5rem; }
    .pct { font-weight: 700; color: var(--accent); font-size: 0.9rem; }
    .bar { height: 6px; border-radius: 3px; background: var(--line); margin: 0.3rem 0; overflow: hidden; }
    .bar i { display: block; height: 100%; background: var(--accent); border-radius: 3px; }
    .role p { margin: 0; font-size: 0.85rem; color: var(--muted); }
    .offers-btn {
      margin-block-start: 0.45rem;
      font: inherit;
      font-size: 0.8rem;
      font-weight: 700;
      padding: 0.35rem 0.8rem;
      border-radius: 999px;
      border: 1.5px solid var(--accent);
      background: transparent;
      color: var(--accent);
      cursor: pointer;
    }
    .offers-btn:disabled { opacity: 0.6; cursor: progress; }
    .offer-list { list-style: none; margin: 0.6rem 0 0; padding: 0; display: flex; flex-direction: column; gap: 0.4rem; }
    .offer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.6rem;
      padding: 0.55rem 0.7rem;
      border: 1px solid var(--glass-border);
      border-radius: 10px;
      background: var(--chalk);
    }
    .offer-main { display: flex; flex-direction: column; min-width: 0; }
    .offer-main strong { font-size: 0.9rem; }
    .offer-co { font-size: 0.8rem; color: var(--muted); }
    .offer-side { display: flex; flex-direction: column; align-items: flex-end; gap: 0.25rem; flex: 0 0 auto; font-size: 0.8rem; }
    .offer-side a { color: var(--accent); font-weight: 700; text-decoration: none; }
    .tag { font-size: 0.7rem; font-weight: 600; padding: 0.1rem 0.45rem; border-radius: 999px; background: color-mix(in srgb, var(--accent) 12%, transparent); color: var(--accent); }
    .tag.stage { background: color-mix(in srgb, var(--green) 14%, transparent); color: var(--green); }
    .err-inline { margin: 0.3rem 0 0; color: #ff9a94; font-size: 0.82rem; }

    .exp-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.7rem; }
    .exp { border-inline-start: 3px solid var(--accent); padding-inline-start: 0.7rem; }
    .exp .meta { display: block; font-size: 0.82rem; color: var(--muted); }
    .exp ul { font-size: 0.88rem; }
  `,
})
export class CvWorkspace {
  readonly accent = input<string>('#5b9bea');

  private readonly http = inject(HttpClient);
  protected readonly accepted = ACCEPTED.join(',');
  protected readonly loading = signal(false);
  protected readonly error = signal('');
  protected readonly offers = signal<Record<string, GeoPayload>>({});
  protected readonly offersLoading = signal<Record<string, boolean>>({});
  protected readonly offerError = signal<Record<string, string>>({});
  protected readonly analysis = signal<CvAnalysis | null>(null);

  protected onPick(event: Event): void {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (file) this.upload(file);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    const file = event.dataTransfer?.files?.[0];
    if (file) this.upload(file);
  }

  protected hasCoords(payload: GeoPayload): boolean {
    return payload.items.some((o) => typeof o['lat'] === 'number' && typeof o['lng'] === 'number');
  }

  protected loadOffers(role: string): void {
    this.offersLoading.update((m) => ({ ...m, [role]: true }));
    this.offerError.update((m) => ({ ...m, [role]: '' }));
    this.http
      .get<GeoPayload>('/api/jobs/offers', { params: { what: role } })
      .pipe(finalize(() => this.offersLoading.update((m) => ({ ...m, [role]: false }))))
      .subscribe({
        next: (payload) => this.offers.update((m) => ({ ...m, [role]: payload })),
        error: (err: unknown) => {
          const detail = err instanceof HttpErrorResponse ? err.error?.detail : null;
          this.offerError.update((m) => ({
            ...m,
            [role]: typeof detail === 'string' ? detail : 'Recherche impossible pour le moment.',
          }));
        },
      });
  }

  private upload(file: File): void {
    const ext = '.' + (file.name.split('.').pop() ?? '').toLowerCase();
    if (!ACCEPTED.includes(ext)) {
      this.error.set('Format non supporté : PDF, TXT ou MD uniquement.');
      return;
    }
    const body = new FormData();
    body.set('file', file);
    this.loading.set(true);
    this.error.set('');
    this.http
      .post<CvAnalysis>('/api/cv/analyze', body)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (result) => this.analysis.set(result),
        error: (err: unknown) => {
          const detail = err instanceof HttpErrorResponse ? err.error?.detail : null;
          this.error.set(typeof detail === 'string' ? detail : 'Analyse impossible pour le moment. Réessayez.');
        },
      });
  }
}
