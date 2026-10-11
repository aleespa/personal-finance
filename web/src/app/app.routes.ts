import { Routes } from '@angular/router';

import { holdingsGuard, workbookLoadedGuard } from './core/workbook.guard';

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
      {
        path: 'accounts',
        title: 'Accounts · Personal Finance',
        loadComponent: () => import('./pages/accounts/accounts.page').then((m) => m.AccountsPage),
      },
      {
        path: 'investments',
        title: 'Investments · Personal Finance',
        canActivate: [holdingsGuard],
        loadComponent: () =>
          import('./pages/investments/investments.page').then((m) => m.InvestmentsPage),
      },
      {
        path: 'transactions',
        title: 'Transactions · Personal Finance',
        loadComponent: () =>
          import('./pages/transactions/transactions.page').then((m) => m.TransactionsPage),
      },
      { path: '', pathMatch: 'full', redirectTo: 'overview' },
    ],
  },
  { path: '**', redirectTo: '' },
];
