import { DOCUMENT, Injectable, effect, inject, signal } from '@angular/core';

export type ThemeMode = 'light' | 'dark';

/**
 * Light/dark mode. Starts from the OS preference and follows it until the
 * user picks one with the toolbar toggle. Material's theme is built on CSS
 * light-dark(), so switching `color-scheme` on <html> restyles everything.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly media = this.document.defaultView?.matchMedia?.('(prefers-color-scheme: dark)');
  private userChoice = false;

  readonly mode = signal<ThemeMode>(this.media?.matches ? 'dark' : 'light');

  constructor() {
    this.media?.addEventListener('change', (event) => {
      if (!this.userChoice) {
        this.mode.set(event.matches ? 'dark' : 'light');
      }
    });
    effect(() => {
      this.document.documentElement.style.colorScheme = this.mode();
      this.document.documentElement.dataset['theme'] = this.mode();
    });
  }

  toggle(): void {
    this.userChoice = true;
    this.mode.update((mode) => (mode === 'dark' ? 'light' : 'dark'));
  }
}
