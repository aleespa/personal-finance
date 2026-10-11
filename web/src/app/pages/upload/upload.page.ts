import { HttpErrorResponse } from '@angular/common/http';
import { ChangeDetectionStrategy, Component, inject, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { Router } from '@angular/router';

import { ApiService } from '../../core/api.service';
import { WorkbookService } from '../../core/workbook.service';
import { errorMessage } from '../../shared/errors';

interface UploadError {
  heading: string;
  problems: string[];
}

@Component({
  selector: 'app-upload-page',
  imports: [MatButtonModule, MatCardModule, MatIconModule, MatProgressSpinnerModule],
  templateUrl: './upload.page.html',
  styleUrl: './upload.page.scss',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UploadPage {
  private readonly api = inject(ApiService);
  private readonly workbook = inject(WorkbookService);
  private readonly router = inject(Router);

  protected readonly uploading = signal(false);
  protected readonly dragging = signal(false);
  protected readonly fileName = signal<string | null>(null);
  protected readonly error = signal<UploadError | null>(null);

  protected onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    input.value = '';
    if (file) {
      this.upload(file);
    }
  }

  protected onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(true);
  }

  protected onDrop(event: DragEvent): void {
    event.preventDefault();
    this.dragging.set(false);
    const file = event.dataTransfer?.files[0];
    if (file) {
      this.upload(file);
    }
  }

  upload(file: File): void {
    if (this.uploading()) {
      return;
    }
    this.fileName.set(file.name);
    this.error.set(null);
    this.uploading.set(true);
    this.api.uploadWorkbook(file).subscribe({
      next: (meta) => {
        this.workbook.meta.set(meta);
        void this.router.navigateByUrl('/overview');
      },
      error: (error: unknown) => {
        this.uploading.set(false);
        this.error.set(toUploadError(error));
      },
    });
  }
}

/**
 * Validation errors arrive as "Sheet 'X' has problems:\n- problem\n- problem"
 * (see personal_finance/schemas.py). Show the first line as a heading and the
 * rest as a list.
 */
export function toUploadError(error: unknown): UploadError {
  const message = errorMessage(error) ?? 'Upload failed.';
  if (!(error instanceof HttpErrorResponse) || error.status !== 422) {
    return { heading: message, problems: [] };
  }
  const [heading, ...rest] = message.split('\n');
  return {
    heading,
    problems: rest.map((line) => line.replace(/^-\s*/, '')).filter((line) => line.length > 0),
  };
}
