import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TriagemService } from './triagem.service';
import { environment } from '../../environments/environment';

describe('TriagemService', () => {
  let service: TriagemService;
  let httpMock: HttpTestingController;
  let appRef: ApplicationRef;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(TriagemService);
    httpMock = TestBed.inject(HttpTestingController);
    appRef = TestBed.inject(ApplicationRef);
  });

  afterEach(() => {
    httpMock.verify();
  });

  function completarDados(nome: string, endereco: string, idade: number) {
    service.setNomeCompleto(nome);
    service.setEndereco(endereco);
    service.confirmIdade(idade);
    TestBed.tick();
  }

  it('envia POST /start_session com o payload correto ao confirmar idade', async () => {
    completarDados('Ana Souza', 'Rua A, 1', 30);

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/start_session`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ nome_completo: 'Ana Souza', endereco: 'Rua A, 1', idade: 30 });

    req.flush({ session_id: 'session-1', message: 'ok' });
    await appRef.whenStable();

    expect(service.sessionId()).toBe('session-1');
  });

  it('reset() seguido de um novo atendimento não vaza o session_id da sessão anterior', async () => {
    completarDados('Ana Souza', 'Rua A, 1', 30);
    httpMock.expectOne(`${environment.apiBaseUrl}/start_session`).flush({
      session_id: 'session-antiga',
      message: 'ok',
    });
    await appRef.whenStable();
    expect(service.sessionId()).toBe('session-antiga');

    service.reset();
    TestBed.tick();

    completarDados('Bruno Lima', 'Rua B, 2', 40);

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/start_session`);
    expect(req.request.body).toEqual({ nome_completo: 'Bruno Lima', endereco: 'Rua B, 2', idade: 40 });
    req.flush({ session_id: 'session-nova', message: 'ok' });
    await appRef.whenStable();

    expect(service.sessionId()).toBe('session-nova');
  });
});
