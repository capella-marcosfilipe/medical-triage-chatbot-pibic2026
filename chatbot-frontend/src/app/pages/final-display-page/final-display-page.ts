import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { TriagemService } from '../../services/triagem.service';
import { SmartwatchService } from '../../services/smartwatch.service';
import { NemotronChatService } from '../../services/nemotron-chat.service';
import { ChatFlowService } from '../../services/chat-flow.service';

@Component({
  selector: 'app-final-display-page',
  imports: [FullscreenStage, ButtonPrimary],
  templateUrl: './final-display-page.html',
  styleUrl: './final-display-page.css',
})
export class FinalDisplayPage {
  private readonly router = inject(Router);
  private readonly chatFlow = inject(ChatFlowService);
  protected readonly triagem = inject(TriagemService);
  protected readonly smartwatch = inject(SmartwatchService);
  protected readonly chat = inject(NemotronChatService);

  novoAtendimento(): void {
    this.triagem.reset();
    this.smartwatch.reset();
    this.chat.reset();
    this.chatFlow.reset();
    this.router.navigate(['/welcome']);
  }
}
