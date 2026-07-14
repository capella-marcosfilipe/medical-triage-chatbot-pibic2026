import { Routes } from '@angular/router';
import { chatFlowStepGuard } from './guards/chat-flow-step.guard';

export const routes: Routes = [
  { path: '', pathMatch: 'full', redirectTo: 'welcome' },
  {
    path: 'welcome',
    loadComponent: () => import('./pages/welcome-page/welcome-page').then((m) => m.WelcomePage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'welcome' },
  },
  {
    path: 'lgpd',
    loadComponent: () => import('./pages/lgpd-page/lgpd-page').then((m) => m.LgpdPage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'lgpd' },
  },
  {
    path: 'paciente/nome',
    loadComponent: () => import('./pages/ask-name-page/ask-name-page').then((m) => m.AskNamePage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'ask_name' },
  },
  {
    path: 'paciente/endereco',
    loadComponent: () =>
      import('./pages/ask-address-page/ask-address-page').then((m) => m.AskAddressPage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'ask_address' },
  },
  {
    path: 'paciente/idade',
    loadComponent: () => import('./pages/ask-age-page/ask-age-page').then((m) => m.AskAgePage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'ask_age' },
  },
  {
    path: 'atendimento/iniciando',
    loadComponent: () =>
      import('./pages/init-backend-page/init-backend-page').then((m) => m.InitBackendPage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'init_backend' },
  },
  {
    path: 'atendimento/smartwatch',
    loadComponent: () =>
      import('./pages/smartwatch-loading-page/smartwatch-loading-page').then(
        (m) => m.SmartwatchLoadingPage,
      ),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'smartwatch_loading' },
  },
  {
    path: 'atendimento/chat',
    loadComponent: () =>
      import('./pages/nemotron-chat-page/nemotron-chat-page').then((m) => m.NemotronChatPage),
    canActivate: [chatFlowStepGuard],
    data: { flowState: 'nemotron_chat' },
  },
  { path: '**', redirectTo: 'welcome' },
];
