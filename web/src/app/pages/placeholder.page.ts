import { ChangeDetectionStrategy, Component } from '@angular/core';

/** Stand-in for the Accounts, Investments and Transactions tabs until Phase 4. */
@Component({
  selector: 'app-placeholder-page',
  template: `<p>This tab is not built yet.</p>`,
  styles: `p { color: var(--mat-sys-on-surface-variant); }`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlaceholderPage {}
