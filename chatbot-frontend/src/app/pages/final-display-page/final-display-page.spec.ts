import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { FinalDisplayPage } from './final-display-page';
import { TriagemService } from '../../services/triagem.service';
import { SmartwatchService } from '../../services/smartwatch.service';
import { NemotronChatService } from '../../services/nemotron-chat.service';
import { ChatFlowService } from '../../services/chat-flow.service';

describe('FinalDisplayPage', () => {
  const rawAnswer = 'Triagem concluída. Encaminhamento sugerido: Cardiologia.';

  function setup(finalSpecialty: string | undefined, finalOrientation: string | undefined) {
    const triagemStub = { nomeCompleto: () => 'Maria da Silva', reset: vi.fn() };
    const smartwatchStub = { dadosFisiologicos: () => undefined, reset: vi.fn() };
    const chatStub = {
      finalSpecialty: () => finalSpecialty,
      finalOrientation: () => finalOrientation,
      reset: vi.fn(),
    };
    const chatFlowStub = { reset: vi.fn() };
    const routerStub = { navigate: vi.fn() };

    TestBed.configureTestingModule({
      imports: [FinalDisplayPage],
      providers: [
        { provide: TriagemService, useValue: triagemStub },
        { provide: SmartwatchService, useValue: smartwatchStub },
        { provide: NemotronChatService, useValue: chatStub },
        { provide: ChatFlowService, useValue: chatFlowStub },
        { provide: Router, useValue: routerStub },
      ],
    });

    const fixture = TestBed.createComponent(FinalDisplayPage);
    fixture.detectChanges();
    return fixture;
  }

  it('exibe a especialidade e a orientação separadamente, não o texto bruto do answer', () => {
    const fixture = setup('Cardiologia', 'Paciente com dor torácica típica há 2 dias.');
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';

    const especialidadeEl = (fixture.nativeElement as HTMLElement).querySelector('.final-page__specialty');
    expect(especialidadeEl?.textContent?.trim()).toBe('Cardiologia');

    const orientacaoEl = (fixture.nativeElement as HTMLElement).querySelector('.final-page__summary');
    expect(orientacaoEl?.textContent?.trim()).toBe('Paciente com dor torácica típica há 2 dias.');

    // o texto bruto de fechamento do LLM não deve mais aparecer na tela
    expect(texto).not.toContain(rawAnswer);
  });

  it('mostra mensagens de fallback quando specialty/orientation vêm undefined', () => {
    const fixture = setup(undefined, undefined);
    const texto = (fixture.nativeElement as HTMLElement).textContent ?? '';

    expect(texto).toContain('Especialidade não disponível');
    expect(texto).toContain('Orientação não disponível');
  });
});
