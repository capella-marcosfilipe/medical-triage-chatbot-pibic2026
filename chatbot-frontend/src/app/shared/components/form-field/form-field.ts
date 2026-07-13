import { Component, input } from '@angular/core';
import { FormControl, ReactiveFormsModule } from '@angular/forms';

@Component({
  selector: 'app-form-field',
  imports: [ReactiveFormsModule],
  templateUrl: './form-field.html',
  styleUrl: './form-field.css',
})
export class FormField {
  readonly label = input.required<string>();
  readonly inputId = input.required<string>();
  readonly control = input.required<FormControl>();
  readonly type = input<string>('text');
  readonly errorMessage = input<string>('Campo inválido');
}
