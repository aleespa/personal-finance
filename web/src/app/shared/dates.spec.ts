import { parseIsoDate, toIsoDate } from './dates';

describe('dates', () => {
  it('parses ISO dates as local dates', () => {
    const date = parseIsoDate('2025-03-09');
    expect([date.getFullYear(), date.getMonth(), date.getDate()]).toEqual([2025, 2, 9]);
  });

  it('round-trips', () => {
    expect(toIsoDate(parseIsoDate('2024-12-31'))).toBe('2024-12-31');
    expect(toIsoDate(parseIsoDate('2025-01-01'))).toBe('2025-01-01');
  });
});
