import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { NemotronChatService } from './nemotron-chat.service';
import { TriagemService } from './triagem.service';
import { environment } from '../../environments/environment';

describe('NemotronChatService', () => {
  let service: NemotronChatService;
  let triagem: TriagemService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(NemotronChatService);
    triagem = TestBed.inject(TriagemService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    vi.useRealTimers();
  });

  function flushEnqueue(jobId: string, chatId: string) {
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    req.flush({ job_id: jobId, chat_id: chatId, status: 'pending', idempotency_key: 'k', queue: 'q' });
    return req;
  }

  function flushStatusCompleted(
    jobId: string,
    chatId: string,
    answer: string,
    diagnosisStatus: 'ongoing' | 'diagnosis_concluded',
    specialty: string | null = null,
    orientation: string | null = null,
  ) {
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/chat/status/${jobId}`);
    req.flush({
      job_id: jobId,
      chat_id: chatId,
      status: 'completed',
      idempotency_key: 'k',
      created_at: new Date().toISOString(),
      content: { answer, diagnosis_status: diagnosisStatus, specialty, orientation },
    });
  }

  it('usa o session_id do TriagemService como chat_id no primeiro envio', async () => {
    triagem.setNomeCompleto('Ana Souza');
    triagem.setEndereco('Rua A, 1');
    triagem.confirmIdade(30);
    TestBed.tick();
    httpMock.expectOne(`${environment.apiBaseUrl}/start_session`).flush({
      session_id: 'session-abc',
      message: 'ok',
    });
    await TestBed.inject(ApplicationRef).whenStable();

    const promise = service.sendMessage('dor de cabeça');
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    expect(req.request.body.chat_id).toBe('session-abc');
    req.flush({ job_id: 'job-x', chat_id: 'session-abc', status: 'pending', idempotency_key: 'k', queue: 'q' });
    await promise;

    flushStatusCompleted('job-x', 'session-abc', 'Pode detalhar?', 'ongoing');
  });

  it('mostra a saudação inicial fixa antes de qualquer envio', () => {
    expect(service.messages()).toEqual([
      { role: 'assistant', content: 'O que você está sentindo hoje?' },
    ]);
  });

  it('envia queixa muito curta (1 caractere) corretamente', async () => {
    const promise = service.sendMessage('a');
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    expect(req.request.body.message).toBe('a');
    req.flush({ job_id: 'job-1', chat_id: 'chat-1', status: 'pending', idempotency_key: 'k', queue: 'q' });
    await promise;

    flushStatusCompleted('job-1', 'chat-1', 'Pode detalhar mais o sintoma?', 'ongoing');

    const last = service.messages().at(-1);
    expect(last).toEqual({
      role: 'assistant',
      content: 'Pode detalhar mais o sintoma?',
      processingTimeMs: undefined,
    });
    expect(service.isWaitingForReply()).toBe(false);
  });

  it('envia queixa muito longa sem truncar o texto', async () => {
    const longMessage = 'dor '.repeat(1000).trim();
    const promise = service.sendMessage(longMessage);
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    expect(req.request.body.message).toBe(longMessage);
    expect(req.request.body.message.length).toBe(longMessage.length);
    req.flush({ job_id: 'job-2', chat_id: 'chat-2', status: 'pending', idempotency_key: 'k', queue: 'q' });
    await promise;

    flushStatusCompleted('job-2', 'chat-2', 'Entendido, obrigado por detalhar.', 'ongoing');

    expect(service.messages().some((m) => m.role === 'user' && m.content === longMessage)).toBe(true);
  });

  it('marca diagnosisConcluded e guarda specialty/orientation estruturados quando diagnosis_status é diagnosis_concluded', async () => {
    const promise = service.sendMessage('Já fiz os exames pedidos');
    flushEnqueue('job-3', 'chat-3');
    await promise;

    flushStatusCompleted(
      'job-3',
      'chat-3',
      'Triagem concluída.',
      'diagnosis_concluded',
      'Clínica Geral',
      'Paciente relata fadiga persistente há duas semanas.',
    );

    expect(service.diagnosisConcluded()).toBe(true);
    expect(service.finalSpecialty()).toBe('Clínica Geral');
    expect(service.finalOrientation()).toBe('Paciente relata fadiga persistente há duas semanas.');
  });

  it('finalSpecialty/finalOrientation ficam undefined quando o backend retorna null (ex.: falha de parsing)', async () => {
    const promise = service.sendMessage('Já fiz os exames pedidos');
    flushEnqueue('job-3b', 'chat-3b');
    await promise;

    flushStatusCompleted('job-3b', 'chat-3b', 'Triagem concluída.', 'diagnosis_concluded', null, null);

    expect(service.diagnosisConcluded()).toBe(true);
    expect(service.finalSpecialty()).toBeUndefined();
    expect(service.finalOrientation()).toBeUndefined();
  });

  it('trata falha de rede ao enviar mensagem e permite tentar novamente', async () => {
    const promise = service.sendMessage('estou passando mal');
    const req = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    req.error(new ProgressEvent('network error'));
    await promise;

    expect(service.error()).toBe(
      'Falha de conexão com a assistente virtual. Verifique sua internet e tente novamente.',
    );
    expect(service.isWaitingForReply()).toBe(false);

    const retryPromise = service.retry();
    const retryReq = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    expect(retryReq.request.body.message).toBe('estou passando mal');
    // only one copy of the user message should be in history, not a duplicate
    expect(service.messages().filter((m) => m.content === 'estou passando mal').length).toBe(1);

    retryReq.flush({ job_id: 'job-4', chat_id: 'chat-4', status: 'pending', idempotency_key: 'k', queue: 'q' });
    await retryPromise;
    flushStatusCompleted('job-4', 'chat-4', 'Certo, vamos continuar.', 'ongoing');
    expect(service.error()).toBeUndefined();
  });

  it('trata timeout de polling (30s sem completar) com erro amigável', async () => {
    vi.useFakeTimers();
    const nowSpy = vi.spyOn(Date, 'now');
    let currentTime = 1_000_000;
    nowSpy.mockImplementation(() => currentTime);

    const promise = service.sendMessage('dor no peito há uma semana');
    const enqueueReq = httpMock.expectOne(`${environment.apiBaseUrl}/chat`);
    enqueueReq.flush({ job_id: 'job-5', chat_id: 'chat-5', status: 'pending', idempotency_key: 'k', queue: 'q' });
    await promise;

    const statusReq = httpMock.expectOne(`${environment.apiBaseUrl}/chat/status/job-5`);
    statusReq.flush({
      job_id: 'job-5',
      chat_id: 'chat-5',
      status: 'processing',
      idempotency_key: 'k',
      created_at: new Date().toISOString(),
    });

    // jump the clock past the 30s timeout before the next scheduled poll fires
    currentTime += 30_001;
    await vi.advanceTimersByTimeAsync(500);

    expect(service.error()).toBe('A assistente demorou demais para responder. Tente novamente.');
    expect(service.isWaitingForReply()).toBe(false);

    nowSpy.mockRestore();
  });

  it('reset() volta ao estado inicial', async () => {
    const promise = service.sendMessage('teste');
    flushEnqueue('job-6', 'chat-6');
    await promise;
    flushStatusCompleted('job-6', 'chat-6', 'Resumo final.', 'diagnosis_concluded', 'Clínica Geral', 'resumo');
    expect(service.diagnosisConcluded()).toBe(true);

    service.reset();

    expect(service.messages()).toEqual([
      { role: 'assistant', content: 'O que você está sentindo hoje?' },
    ]);
    expect(service.diagnosisConcluded()).toBe(false);
    expect(service.finalSpecialty()).toBeUndefined();
    expect(service.finalOrientation()).toBeUndefined();
    expect(service.error()).toBeUndefined();
  });
});
