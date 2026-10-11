import { httpResource } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';

import { PlotlyFigure } from '../../core/models';
import { WorkbookService } from '../../core/workbook.service';
import { ChartCardComponent } from '../../shared/chart-card.component';

@Component({
  selector: 'app-accounts-page',
  imports: [ChartCardComponent, MatFormFieldModule, MatSelectModule],
  template: `
    <div class="charts">
      <app-chart-card [title]="lineTitle()" [figureResource]="accountLine">
        <mat-form-field controls class="compact-field wide-field" appearance="outline" subscriptSizing="dynamic">
          <mat-label>Account</mat-label>
          <mat-select [(value)]="account">
            <mat-option value="total">All accounts (total)</mat-option>
            @for (id of accountIds(); track id) {
              <mat-option [value]="id">{{ id }}</mat-option>
            }
          </mat-select>
        </mat-form-field>
      </app-chart-card>

      <app-chart-card
        title="Month-end balances by account"
        [figureResource]="byBank"
        [height]="560"
        [rangeSlider]="true"
      />
    </div>
  `,
  styles: `
    .charts { display: grid; gap: 16px; }
    .wide-field { width: 220px; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AccountsPage {
  private readonly workbook = inject(WorkbookService);

  protected readonly accountIds = computed(() =>
    (this.workbook.meta()?.accounts ?? []).map((a) => a.id).sort((a, b) => a.localeCompare(b)),
  );
  protected readonly account = signal('total');
  protected readonly lineTitle = computed(() => {
    const account = this.account() === 'total' ? 'All accounts' : this.account();
    return `${account}: balance (7-day average)`;
  });

  protected readonly accountLine = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/account-line', { account: this.account() }),
  );
  protected readonly byBank = httpResource<PlotlyFigure>(() =>
    this.workbook.request('charts/balances-by-bank'),
  );
}
