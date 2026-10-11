import { httpResource } from '@angular/common/http';
import {
  ChangeDetectionStrategy,
  Component,
  computed,
  inject,
  linkedSignal,
} from '@angular/core';
import { provideNativeDateAdapter } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSelectModule } from '@angular/material/select';
import { AgGridAngular } from 'ag-grid-angular';
import {
  AllCommunityModule,
  ColDef,
  ModuleRegistry,
  colorSchemeDark,
  colorSchemeLight,
  themeQuartz,
} from 'ag-grid-community';

import { BalancesTable } from '../../core/models';
import { ThemeService } from '../../core/theme.service';
import { WorkbookService } from '../../core/workbook.service';
import { parseIsoDate, toIsoDate } from '../../shared/dates';
import { errorMessage } from '../../shared/errors';
import { formatGbpPence } from '../../shared/format';

ModuleRegistry.registerModules([AllCommunityModule]);

const GRID_PARAMS = {
  fontFamily: 'Roboto, system-ui, "Segoe UI", sans-serif',
  backgroundColor: 'var(--mat-sys-surface)',
  foregroundColor: 'var(--mat-sys-on-surface)',
  headerBackgroundColor: 'var(--mat-sys-surface-container)',
  borderColor: 'var(--mat-sys-outline-variant)',
  accentColor: 'var(--mat-sys-primary)',
};
const LIGHT_THEME = themeQuartz.withPart(colorSchemeLight).withParams(GRID_PARAMS);
const DARK_THEME = themeQuartz.withPart(colorSchemeDark).withParams(GRID_PARAMS);

type Row = BalancesTable['rows'][number];

@Component({
  selector: 'app-transactions-page',
  imports: [
    AgGridAngular,
    MatDatepickerModule,
    MatFormFieldModule,
    MatIconModule,
    MatProgressBarModule,
    MatSelectModule,
  ],
  providers: [provideNativeDateAdapter()],
  templateUrl: './transactions.page.html',
  styleUrl: './transactions.page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TransactionsPage {
  private readonly workbook = inject(WorkbookService);
  private readonly theme = inject(ThemeService);

  private readonly meta = this.workbook.meta;
  protected readonly minDate = computed(() => parseIsoDate(this.meta()?.date_min ?? '2000-01-01'));
  protected readonly maxDate = computed(() => parseIsoDate(this.meta()?.date_max ?? '2000-01-01'));
  protected readonly accounts = computed(() => this.meta()?.accounts ?? []);

  protected readonly start = linkedSignal<Date | null>(() => this.minDate());
  protected readonly end = linkedSignal<Date | null>(() => this.maxDate());
  protected readonly selected = linkedSignal<string[]>(() =>
    this.accounts()
      .filter((a) => a.status === 'Active')
      .map((a) => a.id),
  );

  protected readonly table = httpResource<BalancesTable>(() => {
    const start = this.start();
    const end = this.end();
    const accounts = this.selected();
    // The range picker sets the start before the end; wait for both. With no
    // accounts selected the server would fall back to all active ones.
    if (!start || !end || accounts.length === 0) {
      return undefined;
    }
    return this.workbook.request('balances', {
      start: toIsoDate(start),
      end: toIsoDate(end),
      accounts,
    });
  });
  protected readonly error = computed(() => errorMessage(this.table.error()));

  /** The latest table, kept while the next one loads. */
  private readonly shown = linkedSignal<BalancesTable | undefined, BalancesTable | undefined>({
    source: () => this.table.value(),
    computation: (next, previous) => next ?? previous?.value,
  });
  protected readonly rows = computed<Row[]>(() =>
    this.selected().length === 0 ? [] : (this.shown()?.rows ?? []),
  );
  protected readonly columns = computed<ColDef<Row>[]>(() =>
    (this.shown()?.columns ?? []).map((column) =>
      column === 'date'
        ? { colId: 'date', headerName: 'Date', valueGetter: (p) => p.data?.['date'], pinned: 'left', width: 130 }
        : {
            // Account ids can contain dots, which `field` would treat as a path.
            colId: column,
            headerName: column,
            valueGetter: (p) => p.data?.[column],
            valueFormatter: (p) => (typeof p.value === 'number' ? formatGbpPence(p.value) : ''),
            type: 'rightAligned',
            cellClass: 'amount',
            flex: 1,
            minWidth: 130,
          },
    ),
  );

  protected readonly gridTheme = computed(() => (this.theme.mode() === 'dark' ? DARK_THEME : LIGHT_THEME));
  protected readonly defaultColDef: ColDef<Row> = { sortable: true, resizable: true };
  protected readonly loading = computed(() => this.table.isLoading());
  protected readonly noAccounts = computed(() => this.selected().length === 0);
}
