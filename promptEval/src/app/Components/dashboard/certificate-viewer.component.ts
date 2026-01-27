import { CommonModule } from '@angular/common';
import { Component, Input } from '@angular/core';
import { Certificate } from '../../models/course.model';

/**
 * CertificateViewer
 * ------------------
 * Lists user certificates with links to view/download.
 */
@Component({
  selector: 'app-certificate-viewer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './certificate-viewer.component.html',
})
export class CertificateViewerComponent {
  @Input() certificates: Certificate[] = [];
  @Input() loading = false;
}
