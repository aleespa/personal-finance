import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';

import { WorkbookMeta } from '../../core/models';
import { WorkbookService } from '../../core/workbook.service';
import { UploadPage } from './upload.page';

const META: WorkbookMeta = {
  id: 'abc',
  accounts: [],
  date_min: '2025-01-01',
  date_max: '2025-03-01',
  years: [2025],
  months: ['2025-03-31'],
  has_holdings: false,
};

describe('UploadPage', () => {
  let http: HttpTestingController;
  let router: Router;

  beforeEach(() => {
    TestBed.configureTestingModule({
      imports: [UploadPage],
      providers: [provideHttpClient(), provideHttpClientTesting(), provideRouter([])],
    });
    http = TestBed.inject(HttpTestingController);
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(true);
  });

  afterEach(() => http.verify());

  function setup() {
    const fixture = TestBed.createComponent(UploadPage);
    const file = new File(['x'], 'book.xlsx');
    fixture.componentInstance.upload(file);
    const request = http.expectOne('/api/workbooks');
    expect(request.request.method).toBe('POST');
    expect((request.request.body as FormData).get('file')).toBe(file);
    return { fixture, request };
  }

  it('stores the workbook and opens the overview', () => {
    const { request } = setup();
    request.flush(META);

    expect(TestBed.inject(WorkbookService).meta()).toEqual(META);
    expect(router.navigateByUrl).toHaveBeenCalledWith('/overview');
  });

  it('lists validation problems', async () => {
    const { fixture, request } = setup();
    request.flush(
      { detail: "Sheet 'Bank A' has problems:\n- 'Balance' is blank in Excel row(s) 3\n- 'Date' is blank" },
      { status: 422, statusText: 'Unprocessable Entity' },
    );
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('.error-heading')?.textContent).toContain(
      "Sheet 'Bank A' has problems:",
    );
    const items = Array.from(element.querySelectorAll('li')).map((li) => li.textContent?.trim());
    expect(items).toEqual(["'Balance' is blank in Excel row(s) 3", "'Date' is blank"]);
    expect(router.navigateByUrl).not.toHaveBeenCalled();
  });

  it('shows a single message for non-validation errors', async () => {
    const { fixture, request } = setup();
    request.flush(null, { status: 500, statusText: 'Server Error' });
    await fixture.whenStable();

    const element = fixture.nativeElement as HTMLElement;
    expect(element.querySelector('.error-heading')?.textContent).toContain('Something went wrong');
    expect(element.querySelectorAll('li').length).toBe(0);
  });
});
