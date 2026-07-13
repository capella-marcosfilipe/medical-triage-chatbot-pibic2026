import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ChatFlowService } from '../services/chat-flow.service';
import { ChatFlowState } from '../models/chat-flow-state';
import { ROUTE_PATH_BY_STATE } from './chat-flow-routes.map';

export const chatFlowStepGuard: CanActivateFn = (route) => {
  const chatFlow = inject(ChatFlowService);
  const router = inject(Router);

  const targetState = route.data['flowState'] as ChatFlowState;

  if (chatFlow.canEnter(targetState)) {
    chatFlow.enter(targetState);
    return true;
  }

  return router.parseUrl(ROUTE_PATH_BY_STATE[chatFlow.current()]);
};
