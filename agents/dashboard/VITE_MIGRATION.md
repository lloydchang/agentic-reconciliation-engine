# Dashboard Frontend - Vite Configuration

This directory contains the React dashboard migrated from Create React App to Vite for improved development experience and build performance.

## Key Improvements with Vite

### 🚀 Performance Benefits
- **Instant HMR** - Hot module replacement that's significantly faster than CRA
- **Optimized builds** - Faster production builds with better tree-shaking
- **Modern ES modules** - Native ES module support in development
- **Lightning-fast dev server** - No bundling required in development

### 🛠️ Developer Experience
- **TypeScript-first** - Better TypeScript support out of the box
- **Path aliases** - Clean imports with `@/` prefix
- **Built-in proxy** - API proxy configuration for backend integration
- **Modern tooling** - Latest versions of Vite, Vitest, and ESLint

### 📦 Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run test` - Run tests with Vitest
- `npm run test:ui` - Run tests with UI
- `npm run lint` - Run ESLint

## Migration Details

### Removed Dependencies
- `react-scripts` - Replaced with Vite
- `web-vitals` - Not essential for current use case
- Old `@types/` packages - Updated to latest versions

### Added Dependencies
- `vite` - Build tool and dev server
- `@vitejs/plugin-react` - React plugin for Vite
- `vitest` - Modern testing framework
- Modern ESLint configuration

### Configuration Files
- `vite.config.ts` - Main Vite configuration
- `tsconfig.json` - Updated for Vite compatibility
- `tsconfig.node.json` - Node.js TypeScript config
- `index.html` - Entry point (moved from public/)
- `src/main.tsx` - React app entry point

## Next Steps

1. Install dependencies: `npm install`
2. Start development: `npm run dev`
3. The app will be available at `http://localhost:3000`

## API Integration

The Vite config includes a proxy that forwards `/api` requests to `http://localhost:5002`, matching the original backend integration.
