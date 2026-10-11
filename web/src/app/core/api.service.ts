import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { WorkbookMeta } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);

  uploadWorkbook(file: File): Observable<WorkbookMeta> {
    const body = new FormData();
    body.append('file', file);
    return this.http.post<WorkbookMeta>('/api/workbooks', body);
  }
}
