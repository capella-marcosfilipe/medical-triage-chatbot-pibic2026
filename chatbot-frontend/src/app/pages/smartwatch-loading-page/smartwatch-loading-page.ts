import { Component, effect, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { Spinner } from '../../shared/components/spinner/spinner';
import { ErrorBanner } from '../../shared/components/error-banner/error-banner';
import { TriagemService } from '../../services/triagem.service';
import { SmartwatchService } from '../../services/smartwatch.service';

const VITALS_DISPLAY_DURATION_MS = 2500;

@Component({
  selector: 'app-smartwatch-loading-page',
  imports: [FullscreenStage, Spinner, ErrorBanner],
  templateUrl: './smartwatch-loading-page.html',
  styleUrl: './smartwatch-loading-page.css',
})
export class SmartwatchLoadingPage {
  private readonly router = inject(Router);
  protected readonly triagem = inject(TriagemService);
  protected readonly smartwatch = inject(SmartwatchService);

  private navigated = false;

  constructor() {
    this.smartwatch.fetch();

    effect(() => {
      const dados = this.smartwatch.dadosFisiologicos();
      if (dados && !this.navigated) {
        this.navigated = true;
        setTimeout(() => this.router.navigate(['/atendimento/chat']), VITALS_DISPLAY_DURATION_MS);
      }
    });
  }

  retry(): void {
    this.smartwatch.retry();
  }
}
