import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideRouter } from '@angular/router';
import { App } from './app';
import { AGENTS, HUBS, agentsOfHub } from './core/agents';
import { UI } from './core/i18n';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      providers: [provideRouter([]), provideHttpClient()],
    }).compileComponents();
  });

  it('should create the app and show the brand', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.brand strong')?.textContent).toContain('Idara');
  });
});

describe('agent catalogue', () => {
  it('mirrors the backend: 4 hubs, 11 agents, each attached to an existing hub', () => {
    expect(HUBS.length).toBe(4);
    expect(AGENTS.length).toBe(11);
    for (const agent of AGENTS) {
      expect(HUBS.some((h) => h.id === agent.hubId)).toBe(true);
    }
    expect(HUBS.map((h) => agentsOfHub(h.id).length)).toEqual([3, 3, 3, 2]);
  });

  it('has every text in the three languages', () => {
    const texts = [
      ...Object.values(UI),
      ...AGENTS.flatMap((a) => [a.name, a.description, ...a.prompts]),
      ...HUBS.flatMap((h) => [h.name, h.description]),
    ];
    for (const t of texts) {
      expect(t.fr.length).toBeGreaterThan(0);
      expect(t.ar.length).toBeGreaterThan(0);
      expect(t.en.length).toBeGreaterThan(0);
    }
  });
});
