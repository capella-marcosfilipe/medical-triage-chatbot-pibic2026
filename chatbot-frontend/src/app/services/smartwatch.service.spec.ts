import { ApplicationRef } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SmartwatchService } from './smartwatch.service';
import { TriagemService } from './triagem.service';
import { environment } from '../../environments/environment';

const SMARTWATCH_URL = `${environment.apiBaseUrl}/get_smartwatch_data/mock-device-001`;

describe('SmartwatchService', () => {
  let service: SmartwatchService;
  let triagem: TriagemService;
  let httpMock: HttpTestingController;
  let appRef: ApplicationRef;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(SmartwatchService);
    triagem = TestBed.inject(TriagemService);
    httpMock = TestBed.inject(HttpTestingController);
    appRef = TestBed.inject(ApplicationRef);
  });

  afterEach(() => {
    httpMock.verify();
  });

  /** Drives TriagemService to a resolved session id, as the app flow does before smartwatch fetch. */
  async function iniciarSessao(sessionId: string): Promise<void> {
    triagem.setNomeCompleto('Ana Souza');
    triagem.setEndereco('Rua A, 1');
    triagem.confirmIdade(30);
    TestBed.tick();
    httpMock.expectOne(`${environment.apiBaseUrl}/start_session`).flush({ session_id: sessionId, message: 'ok' });
    await appRef.whenStable();
  }

  it('busca os dados fisiológicos ao chamar fetch(), enviando o session_id da sessão ativa', async () => {
    await iniciarSessao('session-1');

    service.fetch();
    TestBed.tick();

    const req = httpMock.expectOne(`${SMARTWATCH_URL}?session_id=session-1`);
    expect(req.request.method).toBe('GET');
    req.flush({
      dados_fisiologicos: {
        frequencia_cardiaca: 80,
        saturacao_oxigenio: 98,
        pressao_arterial_sistolica: 120,
        pressao_arterial_diastolica: 80,
        temperatura_corporal: 36.7,
      },
    });
    await appRef.whenStable();

    expect(service.dadosFisiologicos()?.frequencia_cardiaca).toBe(80);
  });

  it('não busca dados enquanto não houver session_id disponível', async () => {
    service.fetch();
    TestBed.tick();

    httpMock.expectNone((r) => r.url.startsWith(SMARTWATCH_URL));
  });

  it('reset() seguido de fetch() busca dados novos em vez de reaproveitar os antigos', async () => {
    await iniciarSessao('session-1');

    service.fetch();
    TestBed.tick();
    httpMock.expectOne(`${SMARTWATCH_URL}?session_id=session-1`).flush({
      dados_fisiologicos: {
        frequencia_cardiaca: 70,
        saturacao_oxigenio: 97,
        pressao_arterial_sistolica: 118,
        pressao_arterial_diastolica: 76,
        temperatura_corporal: 36.5,
      },
    });
    await appRef.whenStable();
    expect(service.dadosFisiologicos()?.frequencia_cardiaca).toBe(70);

    service.reset();
    TestBed.tick();

    service.fetch();
    TestBed.tick();

    const req = httpMock.expectOne(`${SMARTWATCH_URL}?session_id=session-1`);
    req.flush({
      dados_fisiologicos: {
        frequencia_cardiaca: 91,
        saturacao_oxigenio: 96,
        pressao_arterial_sistolica: 125,
        pressao_arterial_diastolica: 82,
        temperatura_corporal: 37.0,
      },
    });
    await appRef.whenStable();

    expect(service.dadosFisiologicos()?.frequencia_cardiaca).toBe(91);
  });
});
