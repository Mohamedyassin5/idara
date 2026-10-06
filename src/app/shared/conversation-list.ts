import { DatePipe, NgTemplateOutlet } from '@angular/common';
import { Component, computed, effect, inject, input, output, signal, untracked } from '@angular/core';
import { ChatService, SessionSummary } from '../core/chat.service';
import { Icon } from '../core/icon';
import { I18n } from '../core/i18n';

/** Saved conversations of one agent: pinned first, then recent, with an archive drawer. */
@Component({
  selector: 'app-conversation-list',
  template: `
    <section class="conv" aria-labelledby="conv-title">
      <header class="conv-head">
        <h2 id="conv-title" class="block-title">{{ i18n.t('convTitle') }}</h2>
        <button type="button" class="btn ghost" (click)="created.emit()">{{ i18n.t('convNew') }}</button>
      </header>

      @if (items().length === 0) {
        <p class="conv-empty">{{ i18n.t('convEmpty') }}</p>
      }

      @if (pinned().length) {
        <h3 class="conv-group">{{ i18n.t('convPinned') }}</h3>
        <ul class="conv-list">
          @for (s of pinned(); track s.session_id) { <ng-container *ngTemplateOutlet="row; context: { $implicit: s }" /> }
        </ul>
      }

      @if (recent().length) {
        <h3 class="conv-group">{{ i18n.t('convRecent') }}</h3>
        <ul class="conv-list">
          @for (s of recent(); track s.session_id) { <ng-container *ngTemplateOutlet="row; context: { $implicit: s }" /> }
        </ul>
      }

      @if (archived().length) {
        <button type="button" class="conv-toggle" [attr.aria-expanded]="showArchived()" (click)="showArchived.set(!showArchived())">
          {{ i18n.t('convArchived') }} ({{ archived().length }})
        </button>
        @if (showArchived()) {
          <ul class="conv-list archived">
            @for (s of archived(); track s.session_id) { <ng-container *ngTemplateOutlet="row; context: { $implicit: s }" /> }
          </ul>
        }
      }
    </section>

    <ng-template #row let-s>
      <li class="conv-item" [class.active]="s.session_id === activeId()">
        <button type="button" class="conv-open" (click)="open.emit(s.session_id)">
          <strong>{{ s.session_name || '…' }}</strong>
          <span class="conv-date">{{ s.updated_at | date: 'd MMM, HH:mm' }}</span>
        </button>
        <div class="conv-actions">
          @if (!s.metadata?.archived) {
            <button
              type="button"
              class="conv-icon"
              [class.on]="!!s.metadata?.pinned"
              [attr.aria-pressed]="!!s.metadata?.pinned"
              [attr.aria-label]="s.metadata?.pinned ? i18n.t('convUnpin') : i18n.t('convPin')"
              [title]="s.metadata?.pinned ? i18n.t('convUnpin') : i18n.t('convPin')"
              (click)="togglePin(s)"
            >
              <app-icon name="thumbtack" />
            </button>
          }
          <button
            type="button"
            class="conv-icon"
            [attr.aria-label]="s.metadata?.archived ? i18n.t('convUnarchive') : i18n.t('convArchive')"
            [title]="s.metadata?.archived ? i18n.t('convUnarchive') : i18n.t('convArchive')"
            (click)="toggleArchive(s)"
          >
            <app-icon name="archive" />
          </button>
          <button
            type="button"
            class="conv-icon danger"
            [attr.aria-label]="i18n.t('convDelete')"
            [title]="i18n.t('convDelete')"
            (click)="remove(s)"
          >
            <app-icon name="trash" />
          </button>
        </div>
      </li>
    </ng-template>
  `,
  imports: [NgTemplateOutlet, DatePipe, Icon],
  styles: `
    .conv { display: flex; flex-direction: column; gap: 0.5rem; }
    .conv-head { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
    .conv-head .block-title { margin: 0; }
    .conv-empty { color: var(--muted); margin: 0; font-size: 0.9rem; }
    .conv-group { margin: 0.4rem 0 0; font-size: 0.78rem; font-weight: 700; color: var(--accent); text-transform: uppercase; letter-spacing: 0.04em; }
    .conv-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 0.4rem; }
    .conv-list.archived { opacity: 0.8; }
    .conv-item {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      padding: 0.6rem 0.75rem;
      background: var(--glass);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
      border: 1px solid var(--glass-border);
      border-radius: 12px;
    }
    .conv-item.active { border-color: var(--accent); box-shadow: 0 0 0 1px var(--accent) inset; }
    .conv-open { all: unset; cursor: pointer; display: flex; flex-direction: column; gap: 0.1rem; min-width: 0; }
    .conv-open strong { font-size: 0.92rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .conv-open:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 6px; }
    .conv-date { font-size: 0.76rem; color: var(--muted); }
    .conv-actions { display: flex; flex-wrap: wrap; gap: 0.3rem; }
    .conv-icon {
      display: inline-grid;
      place-items: center;
      width: 2.1rem;
      height: 2.1rem;
      border-radius: 10px;
      border: 1px solid var(--glass-border);
      background: var(--chalk);
      color: var(--muted);
      cursor: pointer;
      transition: color 0.15s, border-color 0.15s, background 0.15s;
    }
    .conv-icon app-icon { width: 1.1rem; height: 1.1rem; }
    .conv-icon:hover { color: var(--accent); border-color: var(--accent); }
    .conv-icon.on, .conv-icon[aria-pressed='true'] { color: var(--accent); border-color: var(--accent); background: color-mix(in srgb, var(--accent) 10%, transparent); }
    .conv-icon.danger:hover { color: #ff7b74; border-color: #ff7b74; }
    .conv-icon:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
    .conv-toggle { all: unset; cursor: pointer; font-size: 0.82rem; font-weight: 700; color: var(--muted); margin-block-start: 0.3rem; }
  `,
})
export class ConversationList {
  readonly domain = input.required<string>();
  readonly activeId = input<string>('');
  readonly refresh = input<number>(0);
  readonly open = output<string>();
  readonly created = output<void>();

  protected readonly i18n = inject(I18n);
  private readonly chat = inject(ChatService);

  protected readonly items = signal<SessionSummary[]>([]);
  protected readonly showArchived = signal(false);

  protected readonly pinned = computed(() => this.items().filter((s) => s.metadata?.pinned && !s.metadata?.archived));
  protected readonly recent = computed(() => this.items().filter((s) => !s.metadata?.pinned && !s.metadata?.archived));
  protected readonly archived = computed(() => this.items().filter((s) => s.metadata?.archived));

  constructor() {
    effect(() => {
      const domain = this.domain();
      this.refresh();
      untracked(() => this.load(domain));
    });
  }

  protected togglePin(s: SessionSummary): void {
    this.setFlags(s, { pinned: !s.metadata?.pinned, archived: false });
  }

  protected toggleArchive(s: SessionSummary): void {
    this.setFlags(s, { pinned: false, archived: !s.metadata?.archived });
  }

  protected remove(s: SessionSummary): void {
    if (!window.confirm(this.i18n.t('convDeleteConfirm'))) return;
    this.chat.deleteSession(s.session_id).subscribe(() => this.load(this.domain()));
  }

  private setFlags(s: SessionSummary, flags: { pinned: boolean; archived: boolean }): void {
    this.chat.updateFlags(s.session_id, this.domain(), flags).subscribe(() => this.load(this.domain()));
  }

  private load(domain: string): void {
    this.chat.listSessions(domain).subscribe((list) => this.items.set(list));
  }
}
