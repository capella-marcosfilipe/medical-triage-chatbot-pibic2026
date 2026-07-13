import { Injectable, computed, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { PacienteFormData, StartSessionResponse } from '../models/paciente';

@Injectable({ providedIn: 'root' })
export class TriagemService {
  private readonly _nomeCompleto = signal('');
  private readonly _endereco = signal('');
  private readonly _idade = signal<number | null>(null);
  private readonly _pacienteData = signal<PacienteFormData | null>(null);

  readonly nomeCompleto = this._nomeCompleto.asReadonly();
  readonly endereco = this._endereco.asReadonly();
  readonly idade = this._idade.asReadonly();

  setNomeCompleto(valor: string): void {
    this._nomeCompleto.set(valor);
  }

  setEndereco(valor: string): void {
    this._endereco.set(valor);
  }

  confirmIdade(valor: number): void {
    this._idade.set(valor);
    this._pacienteData.set({
      nomeCompleto: this._nomeCompleto(),
      endereco: this._endereco(),
      idade: valor,
    });
  }

  private readonly sessionResource = httpResource<StartSessionResponse>(() => {
    const dados = this._pacienteData();
    if (!dados) {
      return undefined;
    }
    return {
      url: `${environment.apiBaseUrl}/start_session`,
      method: 'POST',
      body: {
        nome_completo: dados.nomeCompleto,
        endereco: dados.endereco,
        idade: dados.idade,
      },
    };
  });

  readonly sessionId = computed(() => {
    if (this.sessionResource.error()) {
      return undefined;
    }
    return this.sessionResource.value()?.session_id;
  });
  readonly isSubmitting = this.sessionResource.isLoading;
  readonly submitError = this.sessionResource.error;

  retry(): void {
    this.sessionResource.reload();
  }
}
