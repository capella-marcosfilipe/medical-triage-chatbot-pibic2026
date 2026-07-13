import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { ButtonPrimary } from '../../shared/components/button-primary/button-primary';
import { IrasutoyaCredit } from '../../shared/components/irasutoya-credit/irasutoya-credit';

@Component({
  selector: 'app-welcome-page',
  imports: [FullscreenStage, ButtonPrimary, IrasutoyaCredit],
  templateUrl: './welcome-page.html',
  styleUrl: './welcome-page.css',
})
export class WelcomePage {
  private readonly router = inject(Router);

  comecar(): void {
    this.router.navigate(['/lgpd']);
  }
}
