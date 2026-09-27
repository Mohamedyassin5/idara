import { Directive, ElementRef, NgZone, OnDestroy, afterNextRender, inject } from '@angular/core';

const SPEED = 0.6; // px per frame (~36 px/s)
const RESUME_MS = 1800;

/**
 * Horizontal carousel that scrolls by itself, loops seamlessly (its content is rendered twice)
 * and can also be moved by hand: mouse drag, touch swipe, trackpad / shift+wheel.
 */
@Directive({ selector: '[appMarquee]' })
export class Marquee implements OnDestroy {
  private readonly el = inject<ElementRef<HTMLElement>>(ElementRef).nativeElement;
  private readonly zone = inject(NgZone);

  private raf = 0;
  private pos = 0;
  private hovering = false;
  private dragging = false;
  private touching = false;
  private resumeTimer: ReturnType<typeof setTimeout> | undefined;
  private startX = 0;
  private startScroll = 0;
  private moved = false;

  constructor() {
    afterNextRender(() => this.zone.runOutsideAngular(() => this.init()));
  }

  private init(): void {
    const el = this.el;
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;

    el.addEventListener('pointerenter', (e) => {
      if (e.pointerType === 'mouse') this.hovering = true;
    });
    el.addEventListener('pointerleave', (e) => {
      if (e.pointerType === 'mouse') this.hovering = false;
    });
    el.addEventListener('pointerdown', (e) => {
      if (e.pointerType === 'mouse') {
        if (e.button !== 0) return;
        this.dragging = true;
        this.moved = false;
        this.startX = e.clientX;
        this.startScroll = el.scrollLeft;
        el.classList.add('dragging');
      } else {
        this.touching = true;
        clearTimeout(this.resumeTimer);
      }
    });
    window.addEventListener('pointermove', (e) => {
      if (!this.dragging) return;
      const dx = e.clientX - this.startX;
      if (Math.abs(dx) > 5) this.moved = true;
      el.scrollLeft = this.startScroll - dx;
    });
    const release = () => {
      if (this.dragging) {
        this.dragging = false;
        el.classList.remove('dragging');
      }
      if (this.touching) {
        clearTimeout(this.resumeTimer);
        this.resumeTimer = setTimeout(() => (this.touching = false), RESUME_MS);
      }
    };
    window.addEventListener('pointerup', release);
    window.addEventListener('pointercancel', release);
    // A drag must not open the card under the cursor.
    el.addEventListener(
      'click',
      (e) => {
        if (this.moved) {
          e.preventDefault();
          e.stopPropagation();
          this.moved = false;
        }
      },
      true,
    );
    el.addEventListener('dragstart', (e) => e.preventDefault());
    el.addEventListener('wheel', () => {
      this.touching = true; // pause while the user scrolls with wheel/trackpad
      clearTimeout(this.resumeTimer);
      this.resumeTimer = setTimeout(() => (this.touching = false), RESUME_MS);
    }, { passive: true });

    if (reduced) return;

    this.pos = el.scrollLeft;
    const tick = () => {
      const half = el.scrollWidth / 2;
      // Someone moved it by hand: follow that position instead of fighting it.
      if (Math.abs(el.scrollLeft - this.pos) > 1.5) this.pos = el.scrollLeft;
      if (!this.hovering && !this.dragging && !this.touching) this.pos += SPEED;
      if (half > 0) {
        if (this.pos >= half) this.pos -= half;
        else if (this.pos < 0) this.pos += half;
      }
      if (Math.abs(el.scrollLeft - this.pos) > 0.01) el.scrollLeft = this.pos;
      this.raf = requestAnimationFrame(tick);
    };
    this.raf = requestAnimationFrame(tick);
  }

  ngOnDestroy(): void {
    cancelAnimationFrame(this.raf);
    clearTimeout(this.resumeTimer);
  }
}
