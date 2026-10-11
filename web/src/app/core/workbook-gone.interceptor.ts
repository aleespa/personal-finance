import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MatSnackBar } from '@angular/material/snack-bar';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { WorkbookService } from './workbook.service';

/**
 * The server keeps one workbook in memory, so a 404 on a workbook URL means it
 * was replaced or the server restarted. Send the user back to upload it.
 */
export const workbookGoneInterceptor: HttpInterceptorFn = (req, next) => {
  const workbook = inject(WorkbookService);
  const router = inject(Router);
  const snackBar = inject(MatSnackBar);

  return next(req).pipe(
    catchError((error: unknown) => {
      if (
        error instanceof HttpErrorResponse &&
        error.status === 404 &&
        req.url.startsWith('/api/workbooks/')
      ) {
        workbook.clear();
        router.navigateByUrl('/upload');
        snackBar.open('The workbook is no longer loaded. Please upload it again.', 'OK', {
          duration: 6000,
        });
      }
      return throwError(() => error);
    }),
  );
};
