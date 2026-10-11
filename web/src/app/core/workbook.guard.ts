import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { WorkbookService } from './workbook.service';

export const workbookLoadedGuard: CanActivateFn = () =>
  inject(WorkbookService).meta() !== null || inject(Router).parseUrl('/upload');

export const holdingsGuard: CanActivateFn = () =>
  inject(WorkbookService).meta()?.has_holdings === true || inject(Router).parseUrl('/overview');
