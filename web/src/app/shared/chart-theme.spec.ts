import { themedLayout } from './chart-theme';

describe('themedLayout', () => {
  const layout = {
    title: { text: 'Server title' },
    height: 500,
    xaxis: { title: { text: 'Date' } },
    yaxis: { tickprefix: '£' },
  };

  it('drops the title and fixed height so the card controls them', () => {
    const themed = themedLayout(layout, 'light');
    expect(themed['title']).toBeUndefined();
    expect(themed['height']).toBeUndefined();
    expect(themed['autosize']).toBe(true);
  });

  it('styles every axis and keeps its settings', () => {
    const light = themedLayout(layout, 'light');
    const dark = themedLayout(layout, 'dark');
    const yaxis = light['yaxis'] as Record<string, unknown>;
    expect(yaxis['tickprefix']).toBe('£');
    expect(yaxis['gridcolor']).toBe('#e1e0d9');
    expect((dark['yaxis'] as Record<string, unknown>)['gridcolor']).toBe('#2c2c2a');
    expect((light['xaxis'] as Record<string, unknown>)['title']).toEqual({
      text: 'Date',
      font: { color: '#52514e' },
    });
  });

  it('adds a range slider on request', () => {
    const themed = themedLayout(layout, 'light', { rangeSlider: true });
    const xaxis = themed['xaxis'] as Record<string, Record<string, unknown>>;
    expect(xaxis['rangeslider']['visible']).toBe(true);
  });

  it('centres a diverging colour scale on zero', () => {
    const themed = themedLayout({ coloraxis: { colorscale: 'RdBu_r' } }, 'dark');
    const coloraxis = themed['coloraxis'] as Record<string, unknown>;
    expect(coloraxis['cmid']).toBe(0);
    expect((coloraxis['colorscale'] as unknown[])[1]).toEqual([0.5, '#383835']);
  });

  it('leaves the input untouched', () => {
    const copy = structuredClone(layout);
    themedLayout(layout, 'dark', { rangeSlider: true });
    expect(layout).toEqual(copy);
  });
});
