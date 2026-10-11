import { HttpResourceRequest } from '@angular/common/http';
import { Injectable, signal } from '@angular/core';

import { WorkbookMeta } from './models';

/** The workbook currently loaded on the server. Lost on page reload by design. */
@Injectable({ providedIn: 'root' })
export class WorkbookService {
  readonly meta = signal<WorkbookMeta | null>(null);

  /**
   * URL of an endpoint of the current workbook, or undefined when none is
   * loaded. Returning undefined from an httpResource request skips the call.
   */
  url(path: string): string | undefined {
    const meta = this.meta();
    return meta ? `/api/workbooks/${meta.id}/${path}` : undefined;
  }

  /** An httpResource request for an endpoint of the current workbook. */
  request(
    path: string,
    params?: Record<string, string | number | readonly (string | number)[]>,
  ): HttpResourceRequest | undefined {
    const url = this.url(path);
    return url === undefined ? undefined : { url, params };
  }

  clear(): void {
    this.meta.set(null);
  }
}
