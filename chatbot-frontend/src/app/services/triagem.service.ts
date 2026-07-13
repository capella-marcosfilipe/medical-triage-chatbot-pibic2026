import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class TriagemService {
  private readonly _nomeCompleto = signal('');
  private readonly _endereco = signal('');
  private readonly _idade = signal<number | null>(null);

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
  }
}
