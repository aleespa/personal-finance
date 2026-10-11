import { ThemeMode } from '../core/theme.service';

/**
 * Chart chrome and colours per theme. Categorical slots come from the
 * dataviz reference palette (validated against Material's azure surfaces);
 * the order is part of its colour-blind safety, so keep it.
 */
const TOKENS = {
  light: {
    ink: '#0b0b0b',
    secondary: '#52514e',
    muted: '#898781',
    grid: '#e1e0d9',
    baseline: '#c3c2b7',
    surface: '#faf9fd',
    divergingMid: '#f0efec',
    colorway: ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#6250d6', '#e34948'],
  },
  dark: {
    ink: '#f0efec',
    secondary: '#c3c2b7',
    muted: '#898781',
    grid: '#2c2c2a',
    baseline: '#383835',
    surface: '#121316',
    divergingMid: '#383835',
    colorway: ['#3987e5', '#d95926', '#199e70', '#c98500', '#d55181', '#008300', '#9085e9', '#e66767'],
  },
} as const;

type Tokens = (typeof TOKENS)[ThemeMode];
type Layout = Record<string, unknown>;

const FONT_FAMILY = 'Roboto, system-ui, "Segoe UI", sans-serif';

export interface ThemeOptions {
  /** Add Plotly's range slider under the x axis. */
  rangeSlider?: boolean;
}

/**
 * Returns `layout` restyled for the theme. The server strips Plotly's template,
 * so this supplies the chrome. The card shows the title, so the figure's own
 * title and fixed height are dropped and the plot fills its container.
 */
export function themedLayout(layout: Layout, mode: ThemeMode, options: ThemeOptions = {}): Layout {
  const t = TOKENS[mode];
  const themed: Layout = {
    ...layout,
    title: undefined,
    height: undefined,
    autosize: true,
    margin: { r: 16, b: 48, l: 64, ...(layout['margin'] as Layout | undefined), t: 16 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    colorway: t.colorway,
    font: { family: FONT_FAMILY, color: t.secondary, size: 12 },
    hoverlabel: {
      bgcolor: t.surface,
      bordercolor: t.baseline,
      font: { family: FONT_FAMILY, color: t.ink },
    },
    legend: {
      ...(layout['legend'] as Layout | undefined),
      bgcolor: 'rgba(0,0,0,0)',
      font: { color: t.secondary },
    },
  };

  for (const key of Object.keys(layout)) {
    if (/^[xy]axis\d*$/.test(key)) {
      themed[key] = themedAxis(layout[key] as Layout, t);
    }
  }
  if (options.rangeSlider) {
    themed['xaxis'] = {
      ...(themed['xaxis'] as Layout | undefined),
      rangeslider: { visible: true, thickness: 0.08, bgcolor: 'rgba(0,0,0,0)', bordercolor: t.baseline },
    };
  }
  if (layout['coloraxis']) {
    // Diverging blue <-> red with a neutral midpoint at zero.
    themed['coloraxis'] = {
      ...(layout['coloraxis'] as Layout),
      cmid: 0,
      colorscale: [
        [0, t.colorway[0]],
        [0.5, t.divergingMid],
        [1, t.colorway[7]],
      ],
      colorbar: { tickfont: { color: t.muted }, outlinewidth: 0 },
    };
  }
  return themed;
}

function themedAxis(axis: Layout | undefined, t: Tokens): Layout {
  const title = axis?.['title'];
  return {
    ...axis,
    gridcolor: t.grid,
    gridwidth: 1,
    zerolinecolor: t.baseline,
    linecolor: t.baseline,
    tickfont: { color: t.muted },
    title:
      typeof title === 'object' && title !== null
        ? { ...(title as Layout), font: { color: t.secondary } }
        : title,
    automargin: true,
  };
}
