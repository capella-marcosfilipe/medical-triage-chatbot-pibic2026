import { Component, inject } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { FormField } from '../../shared/components/form-field/form-field';
import { TriagemService } from '../../services/triagem.service';
import { integerValidator } from '../../shared/validators/integer.validator';

@Component({
  selector: 'app-ask-age-page',
  imports: [FullscreenStage, ButtonPrimary, FormField],
  templateUrl: './ask-age-page.html',
  styleUrl: './ask-age-page.css',
})
export class AskAgePage {
  private readonly router = inject(Router);
  private readonly triagem = inject(TriagemService);

  readonly idadeControl = new FormControl<number | null>(null, {
    validators: [Validators.required, Validators.min(1), Validators.max(120), integerValidator],
  });

  get errorMessage(): string {
    if (this.idadeControl.hasError('required')) {
      return 'Informe sua idade.';
    }
    if (this.idadeControl.hasError('integer')) {
      return 'A idade deve ser um número inteiro.';
    }
    if (this.idadeControl.hasError('min') || this.idadeControl.hasError('max')) {
      return 'A idade deve estar entre 1 e 120 anos.';
    }
    return '';
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    if (this.idadeControl.invalid) {
      this.idadeControl.markAsTouched();
      return;
    }
    this.triagem.confirmIdade(this.idadeControl.value!);
    this.router.navigate(['/atendimento/iniciando']);
  }
}
