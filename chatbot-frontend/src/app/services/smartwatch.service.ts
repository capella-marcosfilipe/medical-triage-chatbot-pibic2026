import { Injectable, computed, signal } from '@angular/core';
import { httpResource } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { SmartwatchDataResponse } from '../models/smartwatch';

// HARDWARE_INTEGRATION: there is no real device pairing yet, so every
// session reads from the same mocked smartwatch id. Once Web Bluetooth /
// Health Connect / HealthKit wiring exists (see smartwatch_simulator.py on
// the backend), this should come from the device-pairing step instead of
// being hardcoded.
const MOCK_SMARTWATCH_ID = 'mock-device-001';

@Injectable({ providedIn: 'root' })
export class SmartwatchService {
  private readonly _shouldFetch = signal(false);

  private readonly dataResource = httpResource<SmartwatchDataResponse>(() => {
    if (!this._shouldFetch()) {
      return undefined;
    }
    return `${environment.apiBaseUrl}/get_smartwatch_data/${MOCK_SMARTWATCH_ID}`;
  });

  readonly dadosFisiologicos = computed(() => {
    if (this.dataResource.error()) {
      return undefined;
    }
    return this.dataResource.value()?.dados_fisiologicos;
  });
  readonly isLoading = this.dataResource.isLoading;
  readonly error = this.dataResource.error;

  fetch(): void {
    this._shouldFetch.set(true);
  }

  retry(): void {
    this.dataResource.reload();
  }

  reset(): void {
    this._shouldFetch.set(false);
  }
}
