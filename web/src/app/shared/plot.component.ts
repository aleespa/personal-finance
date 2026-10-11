import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  effect,
  inject,
  input,
  viewChild,
} from '@angular/core';

import { PlotlyFigure } from '../core/models';
import { ThemeService } from '../core/theme.service';
import { themedLayout } from './chart-theme';

type Plotly = typeof import('plotly.js-dist-min').default;

// plotly.js is ~4.5 MB, so it is loaded on first use instead of in the
// initial bundle.
let plotlyPromise: Promise<Plotly> | undefined;
function loadPlotly(): Promise<Plotly> {
  return (plotlyPromise ??= import('plotly.js-dist-min').then((m) => m.default));
}

const CONFIG = { responsive: true, displaylogo: false, displayModeBar: 'hover' };

@Component({
  selector: 'app-plot',
  template: `<div #host class="plot"></div>`,
  styles: `
    :host { display: block; }
    .plot { width: 100%; height: 100%; }
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PlotComponent {
  readonly figure = input.required<PlotlyFigure>();
  readonly rangeSlider = input(false);

  private readonly host = viewChild.required<ElementRef<HTMLDivElement>>('host');
  private readonly theme = inject(ThemeService);
  private readonly destroyRef = inject(DestroyRef);
  private plotted = false;

  constructor() {
    effect(() => {
      const element = this.host().nativeElement;
      const figure = this.figure();
      const layout = themedLayout(figure.layout, this.theme.mode(), {
        rangeSlider: this.rangeSlider(),
      });
      void loadPlotly().then(async (plotly) => {
        await plotly.react(element, figure.data, layout, CONFIG);
        this.plotted = true;
      });
    });

    afterNextRender(() => {
      const element = this.host().nativeElement;
      const observer = new ResizeObserver(() => {
        if (this.plotted) {
          void loadPlotly().then((plotly) => plotly.Plots.resize(element));
        }
      });
      observer.observe(element);
      this.destroyRef.onDestroy(() => {
        observer.disconnect();
        if (this.plotted) {
          void loadPlotly().then((plotly) => plotly.purge(element));
        }
      });
    });
  }
}
