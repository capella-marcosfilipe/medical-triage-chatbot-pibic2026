import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { IrasutoyaCredit } from '../../shared/components/irasutoya-credit/irasutoya-credit';

@Component({
  selector: 'app-lgpd-page',
  imports: [FullscreenStage, ButtonPrimary, IrasutoyaCredit],
  templateUrl: './lgpd-page.html',
  styleUrl: './lgpd-page.css',
})
export class LgpdPage {
  private readonly router = inject(Router);

  aceitar(): void {
    this.router.navigate(['/paciente/nome']);
  }
}
