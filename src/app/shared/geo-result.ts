import { AfterViewInit, Component, ElementRef, OnDestroy, computed, effect, inject, input, signal, viewChild } from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import * as L from 'leaflet';
import { GeoPayload } from '../core/chat.service';

/** One map pin + one info card, in whatever shape a given result type needs. */
interface Row {
  id: string;
  lat: number;
  lng: number;
  raw: Record<string, unknown>;
}

const TUNISIA_CENTRE: L.LatLngTuple = [34.5, 9.5];

/** One label + one 24x24 stroke-icon body per result type, reused for the map pin and the widget header. */
const KIND: Record<string, { label: string; plural: string; glyph: string }> = {
  parking: {
    label: 'Parking',
    plural: 'parkings repérés',
    glyph: '<path d="M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M9.5 17V7H13a3 3 0 0 1 0 6H9.5"/>',
  },
  souk: {
    label: 'Souk',
    plural: 'marchés repérés',
    glyph: '<path d="M5 12v8.5h14V12"/><path d="M3 9.5 5 4h14l2 5.5M3 9.5a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0"/><path d="M10 20.5V16h4v4.5"/>',
  },
  louage: {
    label: 'Station',
    plural: 'stations de louage',
    glyph: '<path d="M2.5 16V8.5a2 2 0 0 1 2-2H15l5 5V16a1 1 0 0 1-1 1H2.5z"/><path d="M15 6.5v5h5M2.5 11.5h12.5"/><circle cx="7" cy="17.5" r="2"/><circle cx="16.5" cy="17.5" r="2"/>',
  },
  immobilier: {
    label: 'Quartier',
    plural: 'quartiers de référence',
    glyph: '<path d="M5 10.5V20h14v-9.5L12 5z"/><path d="M2.5 11.5 12 3.5l9.5 8M10 20v-5.5h4V20"/>',
  },
  offer: {
    label: 'Offre',
    plural: 'offres trouvées',
    glyph: '<path d="M5 7h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 13h18M11 13v2h2v-2"/>',
  },
  job: {
    label: 'Commerce',
    plural: 'commerces repérés',
    glyph: '<path d="M5 7h14a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2z"/><path d="M9 7V5.5A1.5 1.5 0 0 1 10.5 4h3A1.5 1.5 0 0 1 15 5.5V7M3 13h18M11 13v2h2v-2"/>',
  },
};

interface SortOption {
  key: string;
  label: string;
}

/** Sort choices offered per result type — only the fields that type's data actually has. */
const SORT_OPTIONS: Record<string, SortOption[]> = {
  parking: [
    { key: 'distance', label: 'Proximité' },
    { key: 'name', label: 'Nom' },
  ],
  souk: [
    { key: 'distance', label: 'Proximité' },
    { key: 'name', label: 'Nom' },
  ],
  job: [
    { key: 'distance', label: 'Proximité' },
    { key: 'name', label: 'Nom' },
  ],
  immobilier: [
    { key: 'loyer_asc', label: 'Loyer ↑' },
    { key: 'loyer_desc', label: 'Loyer ↓' },
    { key: 'name', label: 'Nom' },
  ],
  louage: [{ key: 'name', label: 'Nom' }],
  offer: [{ key: 'name', label: 'Titre' }],
};

/**
 * Renders an agent's structured ```geo result (parkings, louage stations, souks, indicative rents…)
 * as an interactive map plus a matching strip of cards — each domain gets its own card layout instead
 * of a generic list, so the result reads like a small purpose-built widget, not a chat bubble.
 */
@Component({
  selector: 'app-geo-result',
  template: `
    <div class="geo" [style.--accent]="accent()">
      <header class="head">
        <span class="head-icon" [innerHTML]="glyph()"></span>
        <span class="head-label">{{ rows().length }} {{ kind().plural }}</span>
        @if (sortOptions().length > 1) {
          <div class="sort" role="group" aria-label="Trier les résultats">
            @for (opt of sortOptions(); track opt.key) {
              <button type="button" [class.active]="sortMode() === opt.key" (click)="sortMode.set(opt.key)">{{ opt.label }}</button>
            }
          </div>
        }
      </header>

      <div class="map" #mapHost></div>

      <ol class="cards" [class]="'kind-' + payload().type">
        @for (row of sortedRows(); track row.id) {
          <li class="card" [class.active]="selected() === row.id" (click)="focus(row)">
            @switch (payload().type) {
              @case ('parking') {
                <span class="badge">P</span>
                <div class="body">
                  <strong>{{ text(row, 'name') }}</strong>
                  <span class="meta">{{ text(row, 'category') }} @if (row.raw['distance_m']) {· {{ row.raw['distance_m'] }} m}</span>
                  @if (text(row, 'address'); as a) { <span class="sub">{{ a }}</span> }
                </div>
              }
              @case ('souk') {
                <span class="badge" [innerHTML]="glyph()"></span>
                <div class="body">
                  <strong>{{ text(row, 'name') }}</strong>
                  <span class="meta">{{ text(row, 'category') }} @if (row.raw['distance_m']) {· {{ row.raw['distance_m'] }} m}</span>
                  @if (text(row, 'address'); as a) { <span class="sub">{{ a }}</span> }
                </div>
              }
              @case ('job') {
                <span class="badge" [innerHTML]="glyph()"></span>
                <div class="body">
                  <strong>{{ text(row, 'name') }}</strong>
                  <span class="meta">{{ text(row, 'category') }} @if (row.raw['distance_m']) {· {{ row.raw['distance_m'] }} m}</span>
                  @if (text(row, 'address'); as a) { <span class="sub">{{ a }}</span> }
                </div>
              }
              @case ('offer') {
                <span class="badge" [innerHTML]="glyph()"></span>
                <div class="body">
                  <strong>{{ text(row, 'name') }}</strong>
                  <span class="meta">{{ text(row, 'company') }}</span>
                  <span class="sub">{{ text(row, 'address') }}</span>
                  <span class="offer-tags">
                    <span class="tag" [class.stage]="text(row, 'category') === 'stage'">{{ text(row, 'category') }}</span>
                    @if (text(row, 'contract')) { <span class="tag">{{ text(row, 'contract') }}</span> }
                  </span>
                  @if (text(row, 'url'); as link) {
                    <a class="apply" [href]="link" target="_blank" rel="noopener">Voir l'offre →</a>
                  }
                </div>
              }
              @case ('louage') {
                <div class="body full">
                  <strong>{{ text(row, 'name') }}</strong>
                  <span class="meta">{{ text(row, 'zone') }}, {{ text(row, 'ville') }}</span>
                  <ul class="tickets">
                    @for (d of destinations(row); track d.to) {
                      <li class="ticket">
                        <span class="to">→ {{ d.to }}</span>
                        <span class="fare">{{ d.tarif_indicatif }}</span>
                        <span class="dur">{{ d.duree_indicative }}</span>
                      </li>
                    }
                  </ul>
                </div>
              }
              @case ('immobilier') {
                <div class="body full">
                  <strong>{{ text(row, 'quartier') }}</strong>
                  <span class="meta">{{ text(row, 'ville') }} · {{ text(row, 'type_dominant') }}</span>
                  <div class="gauge">
                    <div class="fill" [style.left.%]="gaugePos(row, 'loyer_indicatif_min')" [style.width.%]="gaugeWidth(row)"></div>
                  </div>
                  <span class="range">{{ row.raw['loyer_indicatif_min'] }}–{{ row.raw['loyer_indicatif_max'] }} {{ text(row, 'devise') }}</span>
                </div>
              }
            }
          </li>
        }
      </ol>
    </div>
  `,
  styles: `
    .geo {
      margin-block-start: 0.6rem;
      border: 1px solid var(--glass-border);
      border-radius: var(--radius);
      overflow: hidden;
      background: var(--glass);
      backdrop-filter: var(--blur);
      -webkit-backdrop-filter: var(--blur);
      box-shadow: var(--shadow);
    }

    /* A named header gives the widget a fixed, predictable spot in the reply instead of a bare map. */
    .head {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      row-gap: 0.35rem;
      gap: 0.45rem;
      padding: 0.6rem 0.85rem;
      background: var(--glass-strong);
      border-block-end: 1px solid var(--glass-border);
      color: var(--ink);
    }

    .head-icon { color: var(--accent); }

    .sort {
      display: flex;
      gap: 0.35rem;
      margin-inline-start: auto;
    }

    .sort button {
      font: inherit;
      font-size: 0.74rem;
      font-weight: 600;
      padding: 0.3rem 0.65rem;
      border-radius: 999px;
      border: 1px solid var(--glass-border);
      background: transparent;
      color: var(--muted);
      cursor: pointer;
    }

    .sort button:hover:not(.active) {
      background: var(--glass-strong);
      color: var(--ink);
    }

    .sort button.active {
      background: var(--accent);
      color: var(--on-accent);
      border-color: var(--accent);
    }

    .head-icon {
      display: inline-flex;
      width: 1.1rem;
      height: 1.1rem;
    }

    .head-icon ::ng-deep svg {
      width: 100%;
      height: 100%;
    }

    .head-label {
      font-size: 0.82rem;
      font-weight: 700;
      letter-spacing: 0.01em;
    }

    .map {
      height: 240px;
      width: 100%;
      background: var(--sand);
    }

    .cards {
      list-style: none;
      margin: 0;
      padding: 0.7rem;
      display: flex;
      gap: 0.6rem;
      overflow-x: auto;
      scroll-snap-type: x proximity;
    }

    .card {
      scroll-snap-align: start;
      flex: 0 0 auto;
      min-width: 190px;
      max-width: 240px;
      display: flex;
      gap: 0.55rem;
      align-items: flex-start;
      padding: 0.6rem 0.7rem;
      border: 1px solid var(--glass-border);
      border-radius: calc(var(--radius) - 4px);
      cursor: pointer;
      background: var(--chalk);
      transition: border-color 0.15s, transform 0.15s;
    }

    .card:hover {
      transform: translateY(-1px);
    }

    .card.active {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px var(--accent) inset;
    }

    .badge {
      flex: 0 0 auto;
      width: 1.8rem;
      height: 1.8rem;
      border-radius: 50%;
      background: var(--accent);
      color: var(--on-accent);
      display: grid;
      place-items: center;
      font-weight: 700;
      font-size: 0.85rem;
    }

    .badge ::ng-deep svg {
      width: 60%;
      height: 60%;
    }

    .body {
      display: flex;
      flex-direction: column;
      gap: 0.15rem;
      min-width: 0;
    }

    .body.full {
      width: 100%;
    }

    .body strong {
      font-size: 0.92rem;
      color: var(--ink);
    }

    .meta {
      font-size: 0.78rem;
      color: var(--accent);
      font-weight: 600;
    }

    .sub {
      font-size: 0.76rem;
      color: var(--muted);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Louage: destinations as little ticket stubs, evoking a real louage ticket. */
    .tickets {
      list-style: none;
      margin: 0.3rem 0 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      width: 100%;
    }

    .ticket {
      display: flex;
      justify-content: space-between;
      gap: 0.4rem;
      font-size: 0.74rem;
      border-block-start: 1px dashed var(--line);
      padding-block-start: 0.25rem;
    }

    .ticket .to {
      font-weight: 700;
      color: var(--ink);
    }

    .ticket .fare {
      color: var(--accent);
      font-weight: 600;
    }

    .ticket .dur {
      color: var(--muted);
    }

    /* Immobilier: a horizontal rent-range gauge instead of a pin card. */
    .gauge {
      position: relative;
      height: 6px;
      border-radius: 3px;
      background: var(--line);
      width: 100%;
      margin-block-start: 0.3rem;
    }

    .gauge .fill {
      position: absolute;
      inset-block: 0;
      border-radius: 3px;
      background: var(--accent);
    }

    .offer-tags { display: flex; flex-wrap: wrap; gap: 0.25rem; margin-block-start: 0.2rem; }

    .tag {
      font-size: 0.7rem;
      font-weight: 600;
      padding: 0.1rem 0.45rem;
      border-radius: 999px;
      background: color-mix(in srgb, var(--accent) 12%, transparent);
      color: var(--accent);
    }

    .tag.stage { background: color-mix(in srgb, var(--green) 14%, transparent); color: var(--green); }

    .apply {
      margin-block-start: 0.3rem;
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--accent);
    }

    .range {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--accent);
    }

    /* Leaflet builds its own DOM outside Angular's template, so these rules must pierce encapsulation. */
    ::ng-deep .geo-pin {
      display: grid;
      place-items: center;
      width: 28px;
      height: 28px;
      border-radius: 50% 50% 50% 0;
      transform: rotate(-45deg);
      background: var(--accent);
      box-shadow: 0 0 0 1px var(--accent), 0 4px 12px rgb(0 0 0 / 60%);
      border: 2px solid var(--bg);
    }

    ::ng-deep .geo-pin .glyph {
      display: block;
      width: 14px;
      height: 14px;
      color: var(--on-accent);
      transform: rotate(45deg);
    }

    ::ng-deep .geo-pin .glyph svg {
      width: 100%;
      height: 100%;
    }

    ::ng-deep .geo-pin-p {
      transform: rotate(45deg);
      font-weight: 700;
      font-size: 0.8rem;
      color: var(--on-accent);
    }

    /* Restyle Leaflet's default chrome so it reads as part of the app, not a generic embed. */
    ::ng-deep .geo .leaflet-control-zoom {
      border: none !important;
      box-shadow: var(--shadow) !important;
      border-radius: 8px !important;
      overflow: hidden;
    }

    ::ng-deep .geo .leaflet-control-zoom a {
      background: rgb(17 17 19 / 85%) !important;
      color: var(--ink) !important;
      border: none !important;
    }

    ::ng-deep .geo .leaflet-control-zoom a:hover {
      background: var(--sand) !important;
    }

    ::ng-deep .geo .leaflet-popup-content-wrapper,
    ::ng-deep .geo .leaflet-popup-tip {
      background: rgb(17 17 19 / 92%) !important;
      color: var(--ink) !important;
      border: 1px solid var(--glass-border);
    }

    ::ng-deep .geo .leaflet-popup-content-wrapper {
      border-radius: 10px !important;
      box-shadow: var(--shadow) !important;
      backdrop-filter: var(--blur);
    }

    ::ng-deep .geo .leaflet-popup-close-button {
      color: var(--muted) !important;
    }

    /* Dark map: invert the light OSM tiles, then rotate hues back so water stays blue. */
    ::ng-deep .geo .leaflet-tile-pane {
      filter: invert(1) hue-rotate(180deg) brightness(0.92) contrast(0.92) saturate(0.7);
    }

    ::ng-deep .geo .leaflet-container {
      background: var(--bg-elev);
    }

    ::ng-deep .geo .leaflet-popup-content {
      font-family: inherit;
      color: var(--ink);
      margin: 0.55rem 0.7rem;
    }

    ::ng-deep .geo .leaflet-popup-tip {
      box-shadow: none !important;
    }

    ::ng-deep .geo .leaflet-control-attribution {
      background: rgb(0 0 0 / 55%) !important;
      color: var(--muted) !important;
      font-size: 0.66rem !important;
    }
  `,
})
export class GeoResult implements AfterViewInit, OnDestroy {
  readonly payload = input.required<GeoPayload>();
  readonly accent = input<string>('#5b9bea');

  private readonly sanitizer = inject(DomSanitizer);
  private readonly mapHost = viewChild.required<ElementRef<HTMLElement>>('mapHost');
  protected readonly selected = signal<string | null>(null);
  protected readonly sortMode = signal<string>('');

  private map?: L.Map;
  private markers = new Map<string, L.Marker>();

  protected readonly rows = computed<Row[]>(() =>
    this.payload()
      .items.filter((it) => typeof it['lat'] === 'number' && typeof it['lng'] === 'number')
      .map((it) => ({ id: String(it['id'] ?? `${it['lat']},${it['lng']}`), lat: it['lat'] as number, lng: it['lng'] as number, raw: it })),
  );

  protected readonly sortOptions = computed(() => SORT_OPTIONS[this.payload().type] ?? []);

  protected readonly sortedRows = computed<Row[]>(() => {
    const cmp = this.comparator(this.sortMode());
    return cmp ? [...this.rows()].sort(cmp) : this.rows();
  });

  protected readonly kind = computed(() => KIND[this.payload().type] ?? { label: '', plural: 'résultats', glyph: '' });
  private readonly glyphSvg = computed(
    () => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${this.kind().glyph}</svg>`,
  );

  /** The icon as trusted markup for the template: Angular's sanitizer would otherwise strip the <svg> (static, local data). */
  protected readonly glyph = computed(() => this.sanitizer.bypassSecurityTrustHtml(this.glyphSvg()));

  constructor() {
    // A freshly answered question is a new payload object even for the same agent: reset to that type's default sort.
    effect(() => {
      this.sortMode.set(this.sortOptions()[0]?.key ?? '');
    });
    // Re-render markers whenever the rows or accent colour change (accent drives the pin colour).
    effect(() => {
      this.rows();
      this.accent();
      if (this.map) this.renderMarkers();
    });
  }

  ngAfterViewInit(): void {
    this.map = L.map(this.mapHost().nativeElement, { scrollWheelZoom: false }).setView(TUNISIA_CENTRE, 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap',
      maxZoom: 19,
    }).addTo(this.map);
    this.renderMarkers();
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  protected focus(row: Row): void {
    this.selected.set(row.id);
    if (this.map) this.map.flyTo([row.lat, row.lng], 15, { duration: 0.5 });
    this.markers.get(row.id)?.openPopup();
  }

  protected text(row: Row, key: string): string {
    const v = row.raw[key];
    return v == null ? '' : String(v);
  }

  private nameOf(row: Row): string {
    return this.text(row, 'name') || this.text(row, 'quartier');
  }

  private comparator(mode: string): ((a: Row, b: Row) => number) | null {
    switch (mode) {
      case 'distance':
        return (a, b) => (Number(a.raw['distance_m']) || Infinity) - (Number(b.raw['distance_m']) || Infinity);
      case 'name':
        return (a, b) => this.nameOf(a).localeCompare(this.nameOf(b));
      case 'loyer_asc':
        return (a, b) => (Number(a.raw['loyer_indicatif_min']) || 0) - (Number(b.raw['loyer_indicatif_min']) || 0);
      case 'loyer_desc':
        return (a, b) => (Number(b.raw['loyer_indicatif_min']) || 0) - (Number(a.raw['loyer_indicatif_min']) || 0);
      default:
        return null;
    }
  }

  protected destinations(row: Row): { to: string; tarif_indicatif: string; duree_indicative: string }[] {
    return (row.raw['destinations'] as { to: string; tarif_indicatif: string; duree_indicative: string }[] | undefined) ?? [];
  }

  private range(): [number, number] {
    const mins = this.rows().map((r) => Number(r.raw['loyer_indicatif_min']) || 0);
    const maxs = this.rows().map((r) => Number(r.raw['loyer_indicatif_max']) || 0);
    return [0, Math.max(1, ...maxs, ...mins)];
  }

  protected gaugePos(row: Row, key: string): number {
    const [lo, hi] = this.range();
    return (((Number(row.raw[key]) || 0) - lo) / (hi - lo)) * 100;
  }

  protected gaugeWidth(row: Row): number {
    const [lo, hi] = this.range();
    const min = Number(row.raw['loyer_indicatif_min']) || 0;
    const max = Number(row.raw['loyer_indicatif_max']) || 0;
    return ((max - min) / (hi - lo)) * 100;
  }

  private renderMarkers(): void {
    if (!this.map) return;
    for (const m of this.markers.values()) m.remove();
    this.markers.clear();

    const type = this.payload().type;
    const inner = type === 'parking' ? '<span class="geo-pin-p">P</span>' : `<span class="glyph">${this.glyphSvg()}</span>`;
    const icon = L.divIcon({
      className: '',
      html: `<span class="geo-pin" style="--accent:${this.accent()}">${inner}</span>`,
      iconSize: [28, 28],
      iconAnchor: [14, 28],
      popupAnchor: [0, -26],
    });

    const rows = this.rows();
    for (const row of rows) {
      const marker = L.marker([row.lat, row.lng], { icon }).addTo(this.map);
      marker.bindPopup(`<strong>${this.escape(this.nameOf(row))}</strong>`);
      this.markers.set(row.id, marker);
    }
    if (rows.length) {
      this.map.fitBounds(
        rows.map((r) => [r.lat, r.lng] as L.LatLngTuple),
        { padding: [24, 24], maxZoom: 14 },
      );
    }
  }

  private escape(s: string): string {
    return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
  }
}
