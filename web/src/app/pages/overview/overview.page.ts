import { DatePipe } from '@angular/common';
import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';

import { PlotlyFigure, Summary } from '../../core/models';
import { WorkbookService } from '../../core/workbook.service';
import { ChartCardComponent } from '../../shared/chart-card.component';
import { errorMessage } from '../../shared/errors';
import { formatGbp, formatInteger, formatSignedGbp } from '../../shared/format';

@Component({
  selector: 'app-overview-page',
  imports: [
    ChartCardComponent,
    DatePipe,
    MatCardModule,
    MatFormFieldModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSelectModule,
  ],
  templateUrl: './overview.page.html',
  styleUrl: './overview.page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class OverviewPage {
  private readonly workbook = inject(WorkbookService);

  protected readonly months = computed(() => this.workbook.meta()?.months ?? []);
  protected readonly years = computed(() => this.workbook.meta()?.years ?? []);
  protected readonly month = linkedSignal(() => this.months()[0]);
  protected readonly year = linkedSignal(() => this.years()[0]);

  protected readonly summary = httpResource<Summary>(() => this.workbook.url('summary'));
  protected readonly summaryError = computed(() => errorMessage(this.summary.error()));

  protected readonly treemap = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/balance-treemap', { month: this.month() }),
  );

  protected readonly monthlyDiff = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/monthly-diff', { year: this.year() }),
  );

  protected readonly totalLine = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/account-line', { account: 'total' }),
  );

  protected readonly gbp = formatGbp;
  protected readonly signedGbp = formatSignedGbp;
  protected readonly int = formatInteger;
}
