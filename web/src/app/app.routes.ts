import { Routes } from '@angular/router';

import { holdingsGuard, workbookLoadedGuard } from './core/workbook.guard';

const placeholder = () => import('./pages/placeholder.page').then((m) => m.PlaceholderPage);

export const routes: Routes = [
  {
    path: 'upload',
    title: 'Upload · Personal Finance',
    loadComponent: () => import('./pages/upload/upload.page').then((m) => m.UploadPage),
  },
  {
    path: '',
    canActivateChild: [workbookLoadedGuard],
    children: [
      {
        path: 'overview',
        title: 'Overview · Personal Finance',
        loadComponent: () => import('./pages/overview/overview.page').then((m) => m.OverviewPage),
      },
      { path: 'accounts', title: 'Accounts · Personal Finance', loadComponent: placeholder },
      {
        path: 'investments',
        title: 'Investments · Personal Finance',
        canActivate: [holdingsGuard],
        loadComponent: placeholder,
      },
      { path: 'transactions', title: 'Transactions · Personal Finance', loadComponent: placeholder },
      { path: '', pathMatch: 'full', redirectTo: 'overview' },
    ],
  },
  { path: '**', redirectTo: '' },
];
