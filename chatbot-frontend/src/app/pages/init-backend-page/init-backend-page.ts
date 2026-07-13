import { Component, effect, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { Spinner } from '../../shared/components/spinner/spinner';
import { ErrorBanner } from '../../shared/components/error-banner/error-banner';
import { TriagemService } from '../../services/triagem.service';

@Component({
  selector: 'app-init-backend-page',
  imports: [FullscreenStage, Spinner, ErrorBanner],
  templateUrl: './init-backend-page.html',
  styleUrl: './init-backend-page.css',
})
export class InitBackendPage {
  private readonly router = inject(Router);
  protected readonly triagem = inject(TriagemService);

  constructor() {
    effect(() => {
      if (this.triagem.sessionId()) {
        this.router.navigate(['/atendimento/smartwatch']);
      }
    });
  }

  retry(): void {
    this.triagem.retry();
  }
}
