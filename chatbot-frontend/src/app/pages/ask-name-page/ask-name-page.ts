import { Component, inject } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { FormField } from '../../shared/components/form-field/form-field';
import { TriagemService } from '../../services/triagem.service';

@Component({
  selector: 'app-ask-name-page',
  imports: [FullscreenStage, ButtonPrimary, FormField],
  templateUrl: './ask-name-page.html',
  styleUrl: './ask-name-page.css',
})
export class AskNamePage {
  private readonly router = inject(Router);
  private readonly triagem = inject(TriagemService);

  readonly nomeControl = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required, Validators.minLength(3)],
  });

  get errorMessage(): string {
    if (this.nomeControl.hasError('required')) {
      return 'Informe seu nome completo.';
    }
    if (this.nomeControl.hasError('minlength')) {
      return 'O nome deve ter pelo menos 3 letras.';
    }
    return '';
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    if (this.nomeControl.invalid) {
      this.nomeControl.markAsTouched();
      return;
    }
    this.triagem.setNomeCompleto(this.nomeControl.value.trim());
    this.router.navigate(['/paciente/endereco']);
  }
}
