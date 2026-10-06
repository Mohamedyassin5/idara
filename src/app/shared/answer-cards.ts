import { Component, computed, input } from '@angular/core';
import { marked } from 'marked';

interface Section {
  title: string;
  body: string;
  tone: 'hero' | 'docs' | 'price' | 'limit' | 'tip' | 'steps' | 'plain';
}

/** Splits an agent answer on its bold section headers ("**Documents requis**") into cards. */
function splitSections(content: string): Section[] {
  const header = /^\*\*(.+?)\*\*\s*:?\s*/gm;
  const matches = [...content.matchAll(header)];
  if (matches.length === 0) return [{ title: '', body: content.trim(), tone: 'hero' }];

  const sections: Section[] = [];
  const lead = content.slice(0, matches[0].index).trim();
  if (lead) sections.push({ title: '', body: lead, tone: 'hero' });

  matches.forEach((m, i) => {
    const start = (m.index ?? 0) + m[0].length;
    const end = i + 1 < matches.length ? (matches[i + 1].index ?? content.length) : content.length;
    const title = m[1].trim();
    sections.push({ title, body: content.slice(start, end).trim(), tone: toneOf(title) });
  });
  return sections.filter((s) => s.body.length > 0 || s.title);
}

function toneOf(title: string): Section['tone'] {
  const t = title.toLowerCase();
  if (t.startsWith('réponse')) return 'hero';
  if (t.includes('document')) return 'docs';
  if (t.includes('prix') || t.includes('tarif') || t.includes('frais')) return 'price';
  if (t.includes('ne peux pas') || t.includes('ne peux') || t.includes('ne sais')) return 'limit';
  if (t.includes('à savoir') || t.includes('conseil') || t.includes('précaution')) return 'tip';
  if (t.includes('comment') || t.includes('étape') || t.includes('démarche') || t.includes('détail')) return 'steps';
  return 'plain';
}

const ICON: Record<Section['tone'], string> = {
  hero: '✦',
  docs: '▤',
  price: '◈',
  limit: '◌',
  tip: '✚',
  steps: '➜',
  plain: '•',
};

@Component({
  selector: 'app-answer-cards',
  template: `
    <div class="cards" [style.--accent]="accent()">
      @for (s of sections(); track $index) {
        <article class="card" [class]="'tone-' + s.tone">
          @if (s.title) {
            <header>
              <span class="ico" aria-hidden="true">{{ icon(s.tone) }}</span>
              <h3>{{ s.title }}</h3>
            </header>
          }
          <div class="md" [innerHTML]="render(s.body)"></div>
        </article>
      }
    </div>
  `,
  styles: `
    .cards {
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
      padding: 0.95rem 1.05rem;
      box-shadow: var(--shadow);
      min-width: 0;
    }

    .card.tone-hero {
      grid-column: 1 / -1;
      background: var(--glass-strong);
      font-size: 1rem;
    }

    .card header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      margin-block-end: 0.45rem;
    }

    .card h3 {
      margin: 0;
      font-size: 0.92rem;
      font-weight: 700;
      color: var(--accent);
    }

    .ico {
      display: grid;
      place-items: center;
      width: 1.7rem;
      height: 1.7rem;
      border-radius: 50%;
      background: color-mix(in srgb, var(--accent) 14%, transparent);
      color: var(--accent);
      font-size: 0.85rem;
      flex: 0 0 auto;
    }

    .card.tone-docs { border-inline-start: 4px solid var(--green); }
    .card.tone-docs h3, .card.tone-docs .ico { color: var(--green); }
    .card.tone-price { border-inline-start: 4px solid var(--ochre); }
    .card.tone-price h3, .card.tone-price .ico { color: var(--ochre); }
    .card.tone-limit { border-inline-start: 4px solid #8a8f98; background: rgb(255 255 255 / 3%); }
    .card.tone-limit h3, .card.tone-limit .ico { color: #b4b4bb; }
    .card.tone-tip { border-inline-start: 4px solid var(--blue); }
    .card.tone-tip h3, .card.tone-tip .ico { color: var(--blue); }

    .md :first-child { margin-block-start: 0; }
    .md :last-child { margin-block-end: 0; }
    .md p { margin: 0.35rem 0; }
    .md ul, .md ol { padding-inline-start: 1.1rem; margin: 0.3rem 0; }
    .md li { margin-block: 0.2rem; }
    .md a { color: var(--accent); }
  `,
})
export class AnswerCards {
  readonly content = input.required<string>();
  readonly accent = input<string>('#5b9bea');

  protected readonly sections = computed(() => splitSections(this.content()));

  protected render(text: string): string {
    return marked.parse(text, { async: false, breaks: true }) as string; // sanitized by Angular in [innerHTML]
  }

  protected icon(tone: Section['tone']): string {
    return ICON[tone];
  }
}
