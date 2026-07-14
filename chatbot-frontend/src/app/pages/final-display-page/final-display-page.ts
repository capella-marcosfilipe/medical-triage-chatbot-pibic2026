import { Component } from '@angular/core';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { Spinner } from '../../shared/components/spinner/spinner';

@Component({
  selector: 'app-final-display-page',
  imports: [FullscreenStage, Spinner],
  templateUrl: './final-display-page.html',
  styleUrl: './final-display-page.css',
})
export class FinalDisplayPage {}
