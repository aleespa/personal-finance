import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { App } from './app';
import { WorkbookMeta } from './core/models';
import { WorkbookService } from './core/workbook.service';

const META: WorkbookMeta = {
  id: 'abc',
  accounts: [],
  date_min: '2025-01-01',
  date_max: '2025-03-01',
  years: [2025],
  months: ['2025-03-31'],
  has_holdings: false,
};

describe('App', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({ imports: [App], providers: [provideRouter([])] });
  });

  async function render() {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    return fixture.nativeElement as HTMLElement;
  }

  const tabLabels = (element: HTMLElement) =>
    Array.from(element.querySelectorAll('[mat-tab-link]')).map((a) => a.textContent?.trim());

  it('shows no tabs before a workbook is uploaded', async () => {
    const element = await render();
    expect(element.querySelector('.brand')?.textContent).toContain('Personal Finance');
    expect(tabLabels(element)).toEqual([]);
  });

  it('hides the investments tab when there are no holdings', async () => {
    TestBed.inject(WorkbookService).meta.set(META);
    expect(tabLabels(await render())).toEqual(['Overview', 'Accounts', 'Transactions']);
  });

  it('shows the investments tab with holdings', async () => {
    TestBed.inject(WorkbookService).meta.set({ ...META, has_holdings: true });
    expect(tabLabels(await render())).toEqual(['Overview', 'Accounts', 'Investments', 'Transactions']);
  });
});
