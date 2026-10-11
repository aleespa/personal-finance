import { ChangeDetectionStrategy, Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule, MatIconRegistry } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { ThemeService } from './core/theme.service';
import { WorkbookService } from './core/workbook.service';

@Component({
  selector: 'app-root',
  imports: [
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatToolbarModule,
    MatTooltipModule,
    RouterLink,
    RouterLinkActive,
    RouterOutlet,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  protected readonly workbook = inject(WorkbookService);
  protected readonly theme = inject(ThemeService);

  protected readonly tabs = [
    { path: '/overview', label: 'Overview' },
    { path: '/accounts', label: 'Accounts' },
    { path: '/investments', label: 'Investments', holdingsOnly: true },
    { path: '/transactions', label: 'Transactions' },
  ];

  constructor() {
    // index.html loads the Material Symbols font.
    inject(MatIconRegistry).setDefaultFontSetClass('material-symbols-outlined');
  }
}
