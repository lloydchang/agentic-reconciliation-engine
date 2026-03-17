# Dashboard Development Guide

This guide covers setting up and working with the agents dashboard after the Vite migration and directory restructure.

## Quick Start

```bash
cd core/ai/runtime/dashboard
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`.

## Development Workflow

### Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with HMR |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |
| `npm run test` | Run tests with Vitest |
| `npm run test:ui` | Run tests with visual interface |
| `npm run lint` | Run ESLint |

### Development Server

The Vite dev server provides:
- **Instant HMR** - Changes appear immediately
- **API Proxy** - `/api/*` requests proxy to `http://localhost:5002`
- **TypeScript support** - Full type checking
- **Source maps** - Easy debugging

## Architecture

### Directory Structure

```
core/ai/runtime/dashboard/
├── src/
│   ├── components/      # React components
│   ├── App.tsx          # Main dashboard component
│   ├── main.tsx         # React entry point
│   └── test/            # Test setup
├── public/              # Static assets
├── index.html           # HTML entry point
├── vite.config.ts       # Vite configuration
├── tsconfig.json        # TypeScript config
├── package.json         # Dependencies
└── dist/                # Build output (generated)
```

### Key Components

#### App.tsx
Main dashboard component with:
- Agent overview with real-time data
- Performance metrics visualization
- System health monitoring
- Debug tools integration

#### API Integration

The dashboard connects to the Go backend:

```typescript
// Agent data
axios.get('http://localhost:5002/api/core/ai/runtime/detailed')

// Metrics data  
axios.get('http://localhost:5002/api/metrics/real-time')
```

#### Vite Configuration

Key features in `vite.config.ts`:
- React plugin for JSX support
- Path aliases (`@/` for `src/`)
- API proxy for backend integration
- Optimized build configuration

## Styling and Theming

### Material-UI Setup

The dashboard uses Material-UI with custom theming:

```typescript
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
})
```

### Component Styling

Components use Material-UI's `sx` prop for styling:

```typescript
<Box sx={{ p: 3, mb: 2 }}>
  <Typography variant="h4">Dashboard</Typography>
</Box>
```

## Testing

### Vitest Configuration

Tests use Vitest with jsdom environment:

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
  },
})
```

### Writing Tests

```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Dashboard from '../App.tsx'

describe('Dashboard', () => {
  it('renders dashboard title', () => {
    render(<Dashboard />)
    expect(screen.getByText('Cloud AI Agents Dashboard')).toBeInTheDocument()
  })
})
```

## Build and Deployment

### Production Build

```bash
npm run build
```

Output in `dist/` directory:
- Optimized JavaScript and CSS
- Source maps for debugging
- Asset hashing for caching

### Environment Variables

Vite supports environment variables:

```typescript
// In code
const API_URL = import.meta.env.VITE_API_URL

// In .env
VITE_API_URL=http://localhost:5002
```

## Troubleshooting

### Common Issues

1. **Port conflicts** - Vite defaults to port 3000
2. **API connection** - Ensure backend is running on port 5002
3. **TypeScript errors** - Check `tsconfig.json` configuration
4. **Build failures** - Verify all dependencies are installed

### Debug Mode

The dashboard includes debug tools accessible via the bug icon:
- Quick debugging commands
- System health checks
- Agent status information

## Performance

### Optimization Features

- **Code splitting** - Vendor libraries in separate chunks
- **Tree shaking** - Unused code elimination
- **Asset optimization** - Images and fonts optimized
- **Source maps** - Available for development

### Bundle Analysis

To analyze bundle size:

```bash
npm run build
npm run preview
```

Then use browser dev tools to analyze the `dist/` output.

## Migration Notes

### From Create React App

Key differences from CRA:
- No `react-scripts` - uses Vite directly
- Faster HMR and builds
- Modern ES modules
- Different environment variable handling

### Path Changes

Update any references:
- Old: `dashboard-frontend/src/`
- New: `core/ai/runtime/dashboard/src/`

## Future Enhancements

### Potential Additions

1. **PWA support** - Offline capabilities
2. **Component library** - Shared UI components
3. **E2E testing** - Playwright or Cypress
4. **Storybook** - Component documentation
5. **Performance monitoring** - Real user metrics

### Monitoring

Consider adding:
- Error tracking (Sentry)
- Performance monitoring
- User analytics
- A/B testing framework

## Contributing

When contributing to the dashboard:

1. Follow TypeScript best practices
2. Use Material-UI components consistently
3. Write tests for new features
4. Update documentation as needed
5. Test with both light/dark themes

## Support

For dashboard development issues:
1. Check this guide first
2. Review Vite documentation
3. Consult Material-UI docs
4. Check existing GitHub issues
5. Create new issue with detailed description
