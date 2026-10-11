// Only the parts of plotly.js the app uses. The published @types track an
// older major version than the pinned plotly.js-dist-min.
declare module 'plotly.js-dist-min' {
  interface PlotlyStatic {
    react(
      root: HTMLElement,
      data: unknown[],
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>,
    ): Promise<HTMLElement>;
    purge(root: HTMLElement): void;
    Plots: { resize(root: HTMLElement): void };
  }
  const Plotly: PlotlyStatic;
  export default Plotly;
}
