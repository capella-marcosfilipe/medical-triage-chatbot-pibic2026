import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';
import { environment } from '../../environments/environment';
import { ChatEnqueueResponse, ChatMessage, NLPJobStatusResponse } from '../models/chat';

const POLL_INTERVAL_MS = 500;
const POLL_TIMEOUT_MS = 30_000;
const TIMEOUT_MESSAGE = 'A assistente demorou demais para responder. Tente novamente.';
const NETWORK_ERROR_MESSAGE = 'Falha de conexão com a assistente virtual. Verifique sua internet e tente novamente.';
const INITIAL_GREETING = 'O que você está sentindo hoje?';

@Injectable({ providedIn: 'root' })
export class NemotronChatService {
  private readonly http = inject(HttpClient);

  private readonly _messages = signal<ChatMessage[]>([
    { role: 'assistant', content: INITIAL_GREETING },
  ]);
  private readonly _isWaitingForReply = signal(false);
  private readonly _error = signal<string | undefined>(undefined);
  private readonly _diagnosisConcluded = signal(false);
  private readonly _finalAnswer = signal<string | undefined>(undefined);
  private readonly _chatId = signal<string | undefined>(undefined);
  private readonly _lastFailedMessage = signal<string | undefined>(undefined);

  readonly messages = this._messages.asReadonly();
  readonly isWaitingForReply = this._isWaitingForReply.asReadonly();
  readonly error = this._error.asReadonly();
  readonly diagnosisConcluded = this._diagnosisConcluded.asReadonly();
  /**
   * Free-text closing answer from the LLM once diagnosis_status reaches
   * "diagnosis_concluded". There is no separate structured field for
   * especialidade_medica/orientacao_ao_medico in the current backend
   * contract (NLPJobContent only has `answer`), so this raw text is the
   * best available source for both on the final-display screen.
   */
  readonly finalAnswer = this._finalAnswer.asReadonly();

  reset(): void {
    this._messages.set([{ role: 'assistant', content: INITIAL_GREETING }]);
    this._isWaitingForReply.set(false);
    this._error.set(undefined);
    this._diagnosisConcluded.set(false);
    this._finalAnswer.set(undefined);
    this._chatId.set(undefined);
    this._lastFailedMessage.set(undefined);
  }

  async sendMessage(text: string): Promise<void> {
    const trimmed = text.trim();
    if (!trimmed || this._isWaitingForReply()) {
      return;
    }

    this._error.set(undefined);
    this._lastFailedMessage.set(undefined);
    this._messages.update((messages) => [...messages, { role: 'user', content: trimmed }]);
    this._isWaitingForReply.set(true);

    try {
      const response = await firstValueFrom(
        this.http.post<ChatEnqueueResponse>(`${environment.apiBaseUrl}/chat`, {
          message: trimmed,
          engine: 'nemotron',
          chat_id: this._chatId(),
        }),
      );
      this._chatId.set(response.chat_id);
      this.poll(response.job_id, Date.now(), trimmed);
    } catch {
      this.failWith(NETWORK_ERROR_MESSAGE, trimmed);
    }
  }

  retry(): void {
    const lastMessage = this._lastFailedMessage();
    if (!lastMessage) {
      return;
    }
    this._messages.update((messages) => messages.slice(0, -1));
    this._lastFailedMessage.set(undefined);
    void this.sendMessage(lastMessage);
  }

  private poll(jobId: string, startedAt: number, originalMessage: string): void {
    if (Date.now() - startedAt > POLL_TIMEOUT_MS) {
      this.failWith(TIMEOUT_MESSAGE, originalMessage);
      return;
    }

    this.http.get<NLPJobStatusResponse>(`${environment.apiBaseUrl}/chat/status/${jobId}`).subscribe({
      next: (result) => {
        if (result.status === 'completed' && result.content) {
          this._messages.update((messages) => [
            ...messages,
            {
              role: 'assistant',
              content: result.content!.answer,
              processingTimeMs: result.content!.processing_time_ms,
            },
          ]);
          this._isWaitingForReply.set(false);
          if (result.content.diagnosis_status === 'diagnosis_concluded') {
            this._finalAnswer.set(result.content.answer);
            this._diagnosisConcluded.set(true);
          }
        } else if (result.status === 'failed') {
          this.failWith(result.error ?? TIMEOUT_MESSAGE, originalMessage);
        } else {
          setTimeout(() => this.poll(jobId, startedAt, originalMessage), POLL_INTERVAL_MS);
        }
      },
      error: () => this.failWith(NETWORK_ERROR_MESSAGE, originalMessage),
    });
  }

  private failWith(message: string, originalMessage: string): void {
    this._isWaitingForReply.set(false);
    this._error.set(message);
    this._lastFailedMessage.set(originalMessage);
  }
}
