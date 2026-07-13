import { Injectable, signal } from '@angular/core';
import { ChatFlowState, FLOW_ORDER } from '../models/chat-flow-state';

@Injectable({ providedIn: 'root' })
export class ChatFlowService {
  private readonly _current = signal<ChatFlowState>(FLOW_ORDER[0]);
  private readonly _highestReachedIndex = signal(0);

  readonly current = this._current.asReadonly();

  private indexOf(state: ChatFlowState): number {
    return FLOW_ORDER.indexOf(state);
  }

  canEnter(target: ChatFlowState): boolean {
    return this.indexOf(target) <= this._highestReachedIndex() + 1;
  }

  enter(target: ChatFlowState): void {
    if (!this.canEnter(target)) {
      return;
    }
    this._current.set(target);
    const targetIndex = this.indexOf(target);
    if (targetIndex > this._highestReachedIndex()) {
      this._highestReachedIndex.set(targetIndex);
    }
  }
}
