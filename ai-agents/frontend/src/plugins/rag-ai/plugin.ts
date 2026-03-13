import {
  createPlugin,
  createApiFactory,
  createRoutableExtension,
  discoveryApiRef,
  fetchApiRef,
} from '@backstage/core-plugin-api';
import { ragAiApiRef, RagAiApiClient } from './api';
import { rootRouteRef } from './routes';

/**
 * RAG AI plugin for Backstage
 * Provides retrieval-augmented generation capabilities
 */
export const ragAiPlugin = createPlugin({
  id: 'rag-ai',
  apis: [
    createApiFactory({
      api: ragAiApiRef,
      deps: {
        discoveryApi: discoveryApiRef,
        fetchApi: fetchApiRef,
      },
      factory: ({ discoveryApi, fetchApi }) =>
        new RagAiApiClient({ discoveryApi, fetchApi }),
    }),
  ],
  routes: {
    root: rootRouteRef,
  },
});

export const RagAIPage = ragAiPlugin.provide(
  createRoutableExtension({
    name: 'RagAIPage',
    component: () => import('./RagAIPage').then(m => m.RagAIPage),
    mountPoint: rootRouteRef,
  }),
);
