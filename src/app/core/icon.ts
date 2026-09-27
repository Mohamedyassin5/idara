import { Component, computed, input } from '@angular/core';

/**
 * Custom line icons (24x24 grid, round caps) with a soft duotone fill, so every icon shares the same style
 * on every platform, unlike emoji. Shapes flagged `tone` get a translucent fill in the current colour.
 */
interface Shape {
  d?: string;
  circle?: [number, number, number]; // cx, cy, r
  tone?: boolean;
}

const ICONS = {
  // Démarches administratives : dossier avec coin plié et lignes
  document: [
    { d: 'M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z', tone: true },
    { d: 'M14 3v5h5' },
    { d: 'M9 13h6M9 17h4' },
  ],
  // STEG : éclair
  bolt: [{ d: 'M13 2 4.5 13.5H11L10 22l9-12h-6.5z', tone: true }],
  // Entrepreneuriat : fusée
  rocket: [
    { d: 'M12 2.5c3.2 2 5 5.2 5 9l-2 3.5H9L7 11.5c0-3.8 1.8-7 5-9z', tone: true },
    { circle: [12, 9.5, 1.7] },
    { d: 'M9 15l-3.5 2 1 3.5L10 19M15 15l3.5 2-1 3.5L14 19M12 17v4.5' },
  ],
  // Louage : minibus
  van: [
    { d: 'M2.5 16V8.5a2 2 0 0 1 2-2H15l5 5V16a1 1 0 0 1-1 1H2.5z', tone: true },
    { d: 'M15 6.5v5h5M2.5 11.5h12.5' },
    { circle: [7, 17.5, 2] },
    { circle: [16.5, 17.5, 2] },
  ],
  // Stationnement : panneau P
  parking: [
    { d: 'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z', tone: true },
    { d: 'M9.5 17V7H13a3 3 0 0 1 0 6H9.5' },
  ],
  // Souks : étal avec auvent festonné
  market: [
    { d: 'M5 12v8.5h14V12', tone: true },
    { d: 'M3 9.5 5 4h14l2 5.5M3 9.5a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0' },
    { d: 'M10 20.5V16h4v4.5' },
  ],
  // Bac : toque de diplômé
  graduation: [
    { d: 'M2 9.5 12 4.5l10 5-10 5z', tone: true },
    { d: 'M6 12v4.5c0 1.5 2.7 3 6 3s6-1.5 6-3V12M22 9.5V15' },
  ],
  // Emploi : mallette
  briefcase: [
    { d: 'M5 7h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z', tone: true },
    { d: 'M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 13h18M11 13v2h2v-2' },
  ],
  // Kotob : livre
  book: [
    { d: 'M6 3h13v14H6a2 2 0 0 0-2 2V5a2 2 0 0 1 2-2z', tone: true },
    { d: 'M4 19a2 2 0 0 0 2 2h13v-4M9 7.5h6' },
  ],
  // Immobilier : maison
  home: [
    { d: 'M5 10.5V20h14v-9.5L12 5z', tone: true },
    { d: 'M2.5 11.5 12 3.5l9.5 8M10 20v-5.5h4V20' },
  ],
  // Bénévolat : cœur
  heart: [
    { d: 'M12 20.5S3.5 15.5 3.5 9.5A4.5 4.5 0 0 1 12 7.3a4.5 4.5 0 0 1 8.5 2.2c0 6-8.5 11-8.5 11z', tone: true },
  ],
  // Domaines
  landmark: [
    { d: 'M3 9.5 12 3l9 6.5z', tone: true },
    { d: 'M4 21h16M6 9.5V21M10 9.5V21M14 9.5V21M18 9.5V21' },
  ],
  pin: [
    { d: 'M12 21.5s-7-6-7-11.5a7 7 0 0 1 14 0c0 5.5-7 11.5-7 11.5z', tone: true },
    { circle: [12, 10, 2.5] },
  ],
  openbook: [
    { d: 'M2.5 5H8a4 4 0 0 1 4 4v11.5a3 3 0 0 0-3-3H2.5z', tone: true },
    { d: 'M21.5 5H16a4 4 0 0 0-4 4v11.5a3 3 0 0 1 3-3h6.5z' },
  ],
  people: [
    { circle: [9, 8, 3.2], tone: true },
    { d: 'M3 20a6 6 0 0 1 12 0M16.5 5.2a3 3 0 0 1 0 5.6M18 14.5a5.5 5.5 0 0 1 3 5' },
  ],
  // Assistant : boussole
  compass: [
    { circle: [12, 12, 9.5] },
    { d: 'M15.8 8.2 13.5 13.5 8.2 15.8 10.5 10.5z', tone: true },
  ],
  arrow: [{ d: 'M5 12h14M13 6l6 6-6 6' }],
  send: [{ d: 'M21 3 10.5 13.5M21 3l-6.5 18-4-7.5L3 9.5z', tone: true }],
  locate: [
    { circle: [12, 12, 3.5], tone: true },
    { d: 'M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3' },
    { circle: [12, 12, 7.5] },
  ],
} satisfies Record<string, Shape[]>;

export type IconName = keyof typeof ICONS;

@Component({
  selector: 'app-icon',
  template: `
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">
      @for (s of shapes(); track $index) {
        @if (s.circle; as c) {
          <circle [attr.cx]="c[0]" [attr.cy]="c[1]" [attr.r]="c[2]" [attr.fill]="s.tone ? 'currentColor' : 'none'" [class.tone]="s.tone" />
        } @else {
          <path [attr.d]="s.d" [attr.fill]="s.tone ? 'currentColor' : 'none'" [class.tone]="s.tone" />
        }
      }
    </svg>
  `,
  styles: `
    :host {
      display: inline-flex;
      width: 1.5em;
      height: 1.5em;
    }

    svg {
      width: 100%;
      height: 100%;
      stroke-width: var(--icon-stroke, 1.7);
    }

    /* Tone shapes: soft fill; badges raise it (--icon-tone) for a bolder duotone glyph. */
    .tone {
      fill-opacity: var(--icon-tone, 0.16);
    }
  `,
})
export class Icon {
  readonly name = input.required<IconName>();
  protected readonly shapes = computed<Shape[]>(() => ICONS[this.name()]);
}
