export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  processingTimeMs?: number;
}

export interface ChatEnqueueResponse {
  job_id: string;
  chat_id: string;
  status: string;
  idempotency_key: string;
  queue: string;
}

export type DiagnosisStatus = 'ongoing' | 'diagnosis_concluded';

export interface NLPJobContent {
  answer: string;
  processing_time_ms?: number;
  diagnosis_status: DiagnosisStatus;
}

export type NLPJobStatusValue = 'pending' | 'processing' | 'completed' | 'failed';

export interface NLPJobStatusResponse {
  job_id: string;
  chat_id: string;
  status: NLPJobStatusValue;
  idempotency_key: string;
  created_at: string;
  content?: NLPJobContent;
  error?: string;
}
