import { HttpResourceRef } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, computed, input, linkedSignal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { PlotlyFigure } from '../core/models';
import { errorMessage } from './errors';
import { PlotComponent } from './plot.component';

/**
 * A card around one chart: title, optional controls (projected with the
 * `controls` attribute), loading and error states. While a new figure loads
 * the previous one stays visible, dimmed, so the layout doesn't jump.
 */
@Component({
  selector: 'app-chart-card',
  imports: [MatCardModule, MatIconModule, MatProgressSpinnerModule, PlotComponent],
  template: `
    <mat-card appearance="outlined">
      <div class="header">
        <h2>{{ title() }}</h2>
        <div class="controls"><ng-content select="[controls]" /></div>
      </div>
      <div class="body" [style.height.px]="height()">
        @if (error(); as message) {
          <div class="state error" role="alert">
            <mat-icon>error</mat-icon>
            <span>{{ message }}</span>
          </div>
        } @else if (shown(); as figure) {
          <app-plot
            [figure]="figure"
            [rangeSlider]="rangeSlider()"
            [class.stale]="figureResource().isLoading()"
          />
        }
        @if (figureResource().isLoading() && !shown()) {
          <div class="state"><mat-spinner diameter="32" /></div>
        }
      </div>
    </mat-card>
  `,
  styles: `
    :host { display: block; min-width: 0; }
    mat-card { height: 100%; padding: 16px; box-sizing: border-box; }
    .header {
      display: flex; align-items: center; justify-content: space-between;
      gap: 12px; flex-wrap: wrap; min-height: 56px;
    }
    h2 { font: var(--mat-sys-title-medium); color: var(--mat-sys-on-surface); margin: 0; }
    .controls { display: flex; gap: 8px; align-items: center; }
    .body { position: relative; }
    app-plot { height: 100%; transition: opacity 150ms; }
    app-plot.stale { opacity: 0.5; }
    .state {
      position: absolute; inset: 0; display: flex; gap: 8px;
      align-items: center; justify-content: center; text-align: center;
      color: var(--mat-sys-on-surface-variant); font: var(--mat-sys-body-medium);
    }
    .state.error mat-icon { color: var(--mat-sys-error); flex: none; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChartCardComponent {
  readonly title = input.required<string>();
  readonly figureResource = input.required<HttpResourceRef<PlotlyFigure | undefined>>();
  readonly height = input(420);
  readonly rangeSlider = input(false);

  /** The latest figure, kept while the next one loads. */
  protected readonly shown = linkedSignal<PlotlyFigure | undefined, PlotlyFigure | undefined>({
    source: () => this.figureResource().value(),
    computation: (next, previous) => next ?? previous?.value,
  });

  protected readonly error = computed(() => errorMessage(this.figureResource().error()));
}
