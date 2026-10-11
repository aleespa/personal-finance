// Mirrors personal_finance/api/models.py.

export interface AccountInfo {
  id: string;
  bank: string | null;
  type: string;
  currency: string;
  status: 'Active' | 'Closed';
}

export interface WorkbookMeta {
  id: string;
  accounts: AccountInfo[];
  date_min: string;
  date_max: string;
  years: number[];
  months: string[];
  has_holdings: boolean;
}

export interface Summary {
  total_balance: number;
  delta_1y: number;
  total_credit: number;
  active_accounts: number;
  closed_accounts: number;
  debit_accounts: number;
  credit_accounts: number;
  transactions: number;
  unrealized_gains: number | null;
}

export interface BalancesTable {
  columns: string[];
  rows: Record<string, number | string>[];
}

/** A Plotly figure as produced by `fig.to_json()` on the server. */
export interface PlotlyFigure {
  data: Record<string, unknown>[];
  layout: Record<string, unknown>;
}
