import { Component } from '@angular/core';
import { FullscreenStage } from '../../shared/components/fullscreen-stage/fullscreen-stage';
import { Spinner } from '../../shared/components/spinner/spinner';

@Component({
  selector: 'app-nemotron-chat-page',
  imports: [FullscreenStage, Spinner],
  templateUrl: './nemotron-chat-page.html',
  styleUrl: './nemotron-chat-page.css',
})
export class NemotronChatPage {}
