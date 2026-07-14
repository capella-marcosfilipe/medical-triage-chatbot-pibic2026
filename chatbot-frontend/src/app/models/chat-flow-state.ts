export type ChatFlowState =
  | 'welcome'
  | 'lgpd'
  | 'ask_name'
  | 'ask_address'
  | 'ask_age'
  | 'init_backend'
  | 'smartwatch_loading'
  | 'nemotron_chat';

export const FLOW_ORDER: readonly ChatFlowState[] = [
  'welcome',
  'lgpd',
  'ask_name',
  'ask_address',
  'ask_age',
  'init_backend',
  'smartwatch_loading',
  'nemotron_chat',
] as const;
