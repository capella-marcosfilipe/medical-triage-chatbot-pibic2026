export type ChatFlowState =
  | 'welcome'
  | 'lgpd'
  | 'ask_name'
  | 'ask_address'
  | 'ask_age'
  | 'init_backend'
  | 'smartwatch_loading';

export const FLOW_ORDER: readonly ChatFlowState[] = [
  'welcome',
  'lgpd',
  'ask_name',
  'ask_address',
  'ask_age',
  'init_backend',
  'smartwatch_loading',
] as const;
