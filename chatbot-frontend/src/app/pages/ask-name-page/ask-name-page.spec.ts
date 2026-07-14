import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AskNamePage } from './ask-name-page';
import { TriagemService } from '../../services/triagem.service';

describe('AskNamePage', () => {
  let triagemSpy: { setNomeCompleto: ReturnType<typeof vi.fn> };
  let routerSpy: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    triagemSpy = { setNomeCompleto: vi.fn() };
    routerSpy = { navigate: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [AskNamePage],
      providers: [
        { provide: TriagemService, useValue: triagemSpy },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();
  });

  it('aceita nome com caractere especial e acentuação, e avança', () => {
    const fixture = TestBed.createComponent(AskNamePage);
    const page = fixture.componentInstance;
    page.nomeControl.setValue("José D'Ávila-Souza Jr.");

    page.onSubmit(new Event('submit'));

    expect(page.nomeControl.valid).toBe(true);
    expect(triagemSpy.setNomeCompleto).toHaveBeenCalledWith("José D'Ávila-Souza Jr.");
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/paciente/endereco']);
  });

  it('rejeita nome vazio e não avança', () => {
    const fixture = TestBed.createComponent(AskNamePage);
    const page = fixture.componentInstance;
    page.nomeControl.setValue('');

    page.onSubmit(new Event('submit'));

    expect(page.nomeControl.invalid).toBe(true);
    expect(triagemSpy.setNomeCompleto).not.toHaveBeenCalled();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });
});
