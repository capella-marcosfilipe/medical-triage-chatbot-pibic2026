import { Component, inject } from '@angular/core';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { TriagemService } from '../../services/triagem.service';

@Component({
  selector: 'app-smartwatch-loading-page',
  imports: [FullscreenStage],
  templateUrl: './smartwatch-loading-page.html',
  styleUrl: './smartwatch-loading-page.css',
})
export class SmartwatchLoadingPage {
  protected readonly triagem = inject(TriagemService);
}
