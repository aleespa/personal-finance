import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree, provideRouter } from '@angular/router';

import { WorkbookMeta } from './models';
import { holdingsGuard, workbookLoadedGuard } from './workbook.guard';
import { WorkbookService } from './workbook.service';

const META: WorkbookMeta = {
  id: 'abc',
  accounts: [],
  date_min: '2025-01-01',
  date_max: '2025-03-01',
  years: [2025],
  months: ['2025-03-31'],
  has_holdings: false,
};

describe('workbook guards', () => {
  const route = {} as ActivatedRouteSnapshot;
  const state = {} as RouterStateSnapshot;

  beforeEach(() => TestBed.configureTestingModule({ providers: [provideRouter([])] }));

  const run = (guard: typeof workbookLoadedGuard) =>
    TestBed.runInInjectionContext(() => guard(route, state));

  it('sends the user to upload when no workbook is loaded', () => {
    const result = run(workbookLoadedGuard);
    expect(result instanceof UrlTree && result.toString()).toBe('/upload');
  });

  it('allows navigation once a workbook is loaded', () => {
    TestBed.inject(WorkbookService).meta.set(META);
    expect(run(workbookLoadedGuard)).toBe(true);
  });

  it('keeps the investments tab closed without holdings', () => {
    TestBed.inject(WorkbookService).meta.set(META);
    const result = run(holdingsGuard);
    expect(result instanceof UrlTree && result.toString()).toBe('/overview');
  });

  it('opens the investments tab with holdings', () => {
    TestBed.inject(WorkbookService).meta.set({ ...META, has_holdings: true });
    expect(run(holdingsGuard)).toBe(true);
  });
});
