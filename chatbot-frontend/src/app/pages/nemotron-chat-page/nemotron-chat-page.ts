import { Component, effect, inject } from '@angular/core';
import { FormControl, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { Spinner } from '../../shared/components/spinner/spinner';
import { ErrorBanner } from '../../shared/components/error-banner/error-banner';
import { NemotronChatService } from '../../services/nemotron-chat.service';

const RESULT_TRANSITION_DELAY_MS = 1500;

@Component({
  selector: 'app-nemotron-chat-page',
  imports: [ReactiveFormsModule, FullscreenStage, ButtonPrimary, Spinner, ErrorBanner],
  templateUrl: './nemotron-chat-page.html',
  styleUrl: './nemotron-chat-page.css',
})
export class NemotronChatPage {
  private readonly router = inject(Router);
  protected readonly chat = inject(NemotronChatService);

  readonly messageControl = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required],
  });

  private navigated = false;

  constructor() {
    effect(() => {
      if (this.chat.diagnosisConcluded() && !this.navigated) {
        this.navigated = true;
        setTimeout(
          () => this.router.navigate(['/atendimento/resultado']),
          RESULT_TRANSITION_DELAY_MS,
        );
      }
    });
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    if (this.messageControl.invalid) {
      this.messageControl.markAsTouched();
      return;
    }
    const text = this.messageControl.value;
    this.messageControl.reset('');
    void this.chat.sendMessage(text);
  }

  retry(): void {
    this.chat.retry();
  }
}
