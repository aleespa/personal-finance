import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { PlotlyFigure } from '../../core/models';
import { WorkbookService } from '../../core/workbook.service';
import { ChartCardComponent } from '../../shared/chart-card.component';

@Component({
  selector: 'app-investments-page',
  imports: [ChartCardComponent],
  template: `
    <div class="charts">
      <app-chart-card
        class="wide"
        title="Unrealized gain/loss by holding"
        [figureResource]="pnl"
        [height]="520"
        [rangeSlider]="true"
      />
      <app-chart-card
        title="Volatility and correlation (last year)"
        [figureResource]="correlation"
        [height]="460"
      />
      <app-chart-card
        title="Price evolution, indexed to 100 (last year)"
        [figureResource]="evolution"
        [height]="460"
      />
    </div>
  `,
  styles: `
    .charts {
      display: grid;
      grid-template-columns: minmax(0, 2fr) minmax(0, 3fr);
      gap: 16px;
    }
    .wide { grid-column: 1 / -1; }
    @media (max-width: 960px) {
      .charts { grid-template-columns: minmax(0, 1fr); }
    }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class InvestmentsPage {
  private readonly workbook = inject(WorkbookService);

  protected readonly pnl = httpResource<PlotlyFigure>(() => this.workbook.request('charts/holdings-pnl'));
  protected readonly correlation = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/holdings-correlation'),
  );
  protected readonly evolution = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/holdings-evolution'),
  );
}
