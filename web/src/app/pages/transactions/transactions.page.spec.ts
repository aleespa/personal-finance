import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { WorkbookMeta } from '../../core/models';
import { WorkbookService } from '../../core/workbook.service';
import { TransactionsPage } from './transactions.page';

const META: WorkbookMeta = {
  id: 'abc',
  accounts: [
    { id: 'Bank A', bank: 'A', type: 'Current', currency: 'GBP', status: 'Active' },
    { id: 'Old', bank: 'B', type: 'Savings', currency: 'GBP', status: 'Closed' },
    { id: 'Card', bank: 'C', type: 'Credit Card', currency: 'GBP', status: 'Active' },
  ],
  date_min: '2025-01-01',
  date_max: '2025-03-01',
  years: [2025],
  months: ['2025-03-31'],
  has_holdings: false,
};

describe('TransactionsPage', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [TransactionsPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    http = TestBed.inject(HttpTestingController);
    TestBed.inject(WorkbookService).meta.set(META);
  });

  afterEach(() => http.verify());

  it('loads the full date range for active accounts by default', () => {
    TestBed.createComponent(TransactionsPage);
    TestBed.tick();

    const request = http.expectOne((r) => r.url === '/api/workbooks/abc/balances');
    expect(request.request.params.get('start')).toBe('2025-01-01');
    expect(request.request.params.get('end')).toBe('2025-03-01');
    expect(request.request.params.getAll('accounts')).toEqual(['Bank A', 'Card']);
    request.flush({ columns: ['date', 'Bank A', 'Card'], rows: [] });
  });

  it('makes no request when no account is selected', async () => {
    const fixture = TestBed.createComponent(TransactionsPage);
    TestBed.tick();
    http.expectOne((r) => r.url === '/api/workbooks/abc/balances').flush({ columns: ['date'], rows: [] });

    (fixture.componentInstance as unknown as { selected: { set(v: string[]): void } }).selected.set([]);
    await fixture.whenStable();

    http.expectNone((r) => r.url === '/api/workbooks/abc/balances');
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Select at least one account.');
  });
});
