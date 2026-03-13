import { createPlugin, createRoutableExtension, createRouteRef } from '@backstage/core-plugin-api';

export const temporalIntegrationPlugin = createPlugin({
  id: 'temporal-integration',
  routes: {
    root: createRouteRef({
      id: 'temporal-integration:root',
    }),
  },
});

export const TemporalIntegrationPage = temporalIntegrationPlugin.provide(
  createRoutableExtension({
    name: 'TemporalIntegrationPage',
    component: () => import('./components/TemporalPage').then(m => m.TemporalPage),
    mountPoint: temporalIntegrationPlugin.routes.root,
  }),
);
