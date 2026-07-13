import { Component, input, output } from '@angular/core';

@Component({
  selector: 'app-button-primary',
  imports: [],
  templateUrl: './button-primary.html',
  styleUrl: './button-primary.css',
})
export class ButtonPrimary {
  readonly type = input<'button' | 'submit'>('button');
  readonly disabled = input(false);
  readonly pressed = output<void>();
}
