import { Component, inject } from '@angular/core';
import { FormControl, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { FormField } from '../../shared/components/form-field/form-field';
import { TriagemService } from '../../services/triagem.service';

@Component({
  selector: 'app-ask-address-page',
  imports: [FullscreenStage, ButtonPrimary, FormField],
  templateUrl: './ask-address-page.html',
  styleUrl: './ask-address-page.css',
})
export class AskAddressPage {
  private readonly router = inject(Router);
  private readonly triagem = inject(TriagemService);

  readonly enderecoControl = new FormControl('', {
    nonNullable: true,
    validators: [Validators.required],
  });

  get errorMessage(): string {
    if (this.enderecoControl.hasError('required')) {
      return 'Informe seu endereço.';
    }
    return '';
  }

  onSubmit(event: Event): void {
    event.preventDefault();
    if (this.enderecoControl.invalid) {
      this.enderecoControl.markAsTouched();
      return;
    }
    this.triagem.setEndereco(this.enderecoControl.value.trim());
    this.router.navigate(['/paciente/idade']);
  }
}
