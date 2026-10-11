import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { MAT_DATE_LOCALE } from '@angular/material/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { workbookGoneInterceptor } from './core/workbook-gone.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withFetch(), withInterceptors([workbookGoneInterceptor])),
    // Day-first dates in the date pickers.
    { provide: MAT_DATE_LOCALE, useValue: 'en-GB' },
  ],
};
