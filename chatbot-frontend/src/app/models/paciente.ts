export interface PacienteFormData {
  nomeCompleto: string;
  endereco: string;
  idade: number;
}

export interface StartSessionRequest {
  nome_completo: string;
  endereco: string;
  idade: number;
}

export interface StartSessionResponse {
  session_id: string;
  message: string;
}
