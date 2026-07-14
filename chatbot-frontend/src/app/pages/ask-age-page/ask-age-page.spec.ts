import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { AskAgePage } from './ask-age-page';
import { TriagemService } from '../../services/triagem.service';

describe('AskAgePage', () => {
  let triagemSpy: { confirmIdade: ReturnType<typeof vi.fn> };
  let routerSpy: { navigate: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    triagemSpy = { confirmIdade: vi.fn() };
    routerSpy = { navigate: vi.fn() };

    await TestBed.configureTestingModule({
      imports: [AskAgePage],
      providers: [
        { provide: TriagemService, useValue: triagemSpy },
        { provide: Router, useValue: routerSpy },
      ],
    }).compileComponents();
  });

  it.each([1, 120])('aceita idade extrema válida: %i', (idade) => {
    const fixture = TestBed.createComponent(AskAgePage);
    const page = fixture.componentInstance;
    page.idadeControl.setValue(idade);

    page.onSubmit(new Event('submit'));

    expect(page.idadeControl.valid).toBe(true);
    expect(triagemSpy.confirmIdade).toHaveBeenCalledWith(idade);
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/atendimento/iniciando']);
  });

  it.each([0, 121])('rejeita idade fora do intervalo 1-120: %i', (idade) => {
    const fixture = TestBed.createComponent(AskAgePage);
    const page = fixture.componentInstance;
    page.idadeControl.setValue(idade);

    page.onSubmit(new Event('submit'));

    expect(page.idadeControl.invalid).toBe(true);
    expect(triagemSpy.confirmIdade).not.toHaveBeenCalled();
    expect(routerSpy.navigate).not.toHaveBeenCalled();
  });

  it('rejeita idade não inteira', () => {
    const fixture = TestBed.createComponent(AskAgePage);
    const page = fixture.componentInstance;
    page.idadeControl.setValue(30.5);

    page.onSubmit(new Event('submit'));

    expect(page.idadeControl.hasError('integer')).toBe(true);
    expect(triagemSpy.confirmIdade).not.toHaveBeenCalled();
  });
});
