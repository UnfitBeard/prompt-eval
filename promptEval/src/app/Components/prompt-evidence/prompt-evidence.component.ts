import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { AsyncPipe, CommonModule, JsonPipe } from '@angular/common';
import {
  PromptEvalStateService,
  StoredEval,
} from '../../Services/prompt-eval-state.service';

@Component({
  selector: 'app-prompt-evidence',
  imports: [JsonPipe, CommonModule, AsyncPipe],
  templateUrl: './prompt-evidence.component.html',
  styleUrls: ['./prompt-evidence.component.css'],
})
export class PromptEvidenceComponent {
  private state = inject(PromptEvalStateService);
  private router = inject(Router);

  // Observable the template can async-pipe
  resp$ = this.state.last$; // or lastResp$ if you kept the old name

  goBack() {
    this.router.navigate(['/prompt-evaluation']);
  }

  openFull(content: string | undefined) {
    if (!content) return;
    // very small modal: use window.open with a blob for simplicity
    const w = window.open(
      '',
      '_blank',
      'noopener,noreferrer,width=900,height=700'
    );
    if (!w) {
      alert(content);
      return;
    }
    w.document.write(
      '<pre style="white-space:pre-wrap;font-family:monospace;">' +
        this.escapeHtml(content) +
        '</pre>'
    );
    w.document.title = 'Full content';
  }

  exportJson(obj: any, filename = 'prompt-eval.json') {
    const blob = new Blob([JSON.stringify(obj || {}, null, 2)], {
      type: 'application/json',
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  async copyJson(obj: any) {
    try {
      await navigator.clipboard.writeText(JSON.stringify(obj || {}, null, 2));
      // notify user (replace with toast if you have one)
      console.debug('Copied to clipboard');
    } catch (e) {
      console.warn('Copy failed', e);
    }
  }

  private escapeHtml(s: string) {
    return (s || '').replace(
      /[&<>"']/g,
      (c) =>
        ({
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;',
        }[c] || c)
    );
  }
}
