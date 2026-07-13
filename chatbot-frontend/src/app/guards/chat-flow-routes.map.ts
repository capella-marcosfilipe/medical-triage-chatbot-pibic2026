import { ChatFlowState } from '../models/chat-flow-state';

export const ROUTE_PATH_BY_STATE: Record<ChatFlowState, string> = {
  welcome: '/welcome',
  lgpd: '/lgpd',
  ask_name: '/paciente/nome',
  ask_address: '/paciente/endereco',
  ask_age: '/paciente/idade',
  init_backend: '/atendimento/iniciando',
  smartwatch_loading: '/atendimento/smartwatch',
};
