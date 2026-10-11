import { HttpErrorResponse } from '@angular/common/http';

/** A user-facing message for a failed API call. FastAPI puts it in `detail`. */
export function errorMessage(error: unknown): string | null {
  if (!error) {
    return null;
  }
  if (error instanceof HttpErrorResponse) {
    const detail = (error.error as { detail?: unknown } | null)?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (error.status === 0) {
      return 'Could not reach the server. Is it still running?';
    }
  }
  return 'Something went wrong. Please try again.';
}
