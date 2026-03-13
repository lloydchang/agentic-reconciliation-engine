 import { createApp } from '@backstage/app-defaults';
import { FlatRoutes } from '@backstage/core-app-api';
import { discoveryApiRef, createApiFactory } from '@backstage/core-plugin-api';
import { Route, BrowserRouter } from 'react-router-dom';
import { StylesProvider, createGenerateClassName } from '@material-ui/core/styles';
import './utils/makeStyles'; // Import the monkey patch
import { TemporalIntegrationPage } from './plugins/temporal-integration/index';
import { SplitScreenPage } from './components/SplitScreenPage';
import { SplitScreenLandingPage } from './components/SplitScreenLandingPage';
import SkillsManagement from './components/SkillsManagement';
import { Navigation } from './components/Navigation';

// Import RAG AI component
import { RagAiPage } from './plugins/rag-ai';

import {
  CatalogIndexPage,
  CatalogEntityPage,
} from '@backstage/plugin-catalog';
import { CatalogImportPage } from '@backstage/plugin-catalog-import';
import { ScaffolderPage } from '@backstage/plugin-scaffolder';
import { TechDocsIndexPage, TechDocsReaderPage } from '@backstage/plugin-techdocs';
import { UserSettingsPage } from '@backstage/plugin-user-settings';
import { SearchPage } from '@backstage/plugin-search';
// ApiDocsPage and TechRadarPage removed due to React 17 incompatibility

import { TemporalPage } from './plugins/temporal-integration/components/TemporalPage';

const app = createApp({
  apis: [
    createApiFactory({
      api: discoveryApiRef,
      deps: {},
      factory: () => ({
        getBaseUrl: async (pluginId: string) => {
          if (pluginId === 'catalog') {
            return 'http://localhost:8081/api/catalog';
          }
          return `http://localhost:8081/api/${pluginId}`;
        },
      }),
    }),
  ],
  plugins: [],
});

const App = app.createRoot(
  <StylesProvider 
    generateClassName={createGenerateClassName()}
    injectFirst={true}
  >
    <BrowserRouter>
      <Navigation />
      <FlatRoutes>
        <Route path="/" element={<SplitScreenLandingPage />} />
        <Route path="/catalog" element={<CatalogIndexPage />} />
        <Route path="/catalog/:namespace/:kind/:name" element={<CatalogEntityPage />} />
        <Route path="/catalog-import" element={<CatalogImportPage />} />
        <Route path="/docs" element={<TechDocsIndexPage />} />
        <Route path="/docs/:namespace/:kind/:name/*" element={<TechDocsReaderPage />} />
        <Route path="/create" element={<ScaffolderPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/settings" element={<UserSettingsPage />} />
        <Route path="/temporal" element={<TemporalPage />} />
        <Route path="/split-screen" element={<SplitScreenPage />} />
        <Route path="/skills" element={<SkillsManagement />} />
        <Route path="/rag-ai" element={<RagAiPage />} />
      </FlatRoutes>
    </BrowserRouter>
  </StylesProvider>
);

export default App;
