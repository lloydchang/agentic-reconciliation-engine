# Backstage + Temporal Split Screen Integration

## Overview
The split-screen integration provides a seamless way to work with both Backstage and Temporal interfaces simultaneously, eliminating the need to switch between browser tabs or use external split-screen tools.

## Features

### 🖥️ Split Screen View
- **Side-by-side display** of Backstage Catalog and Temporal Web UI
- **Responsive design** that adapts to desktop and mobile screens
- **Independent scrolling** within each panel
- **Real-time synchronization** with both interfaces

### 🔄 Toggle Modes
- **Split View**: View both interfaces side-by-side (desktop only)
- **Backstage Only**: Focus on software catalog and component management
- **Temporal Only**: Focus on workflow execution and monitoring
- **Mobile Toggle**: Easy switching between interfaces on mobile devices

### 📱 Responsive Design
- **Desktop**: Full split-screen experience with 50/50 layout
- **Tablet**: Adaptive layout with optimized panel sizing
- **Mobile**: Single-view mode with quick toggle between interfaces

### ⚡ Performance Features
- **Lazy loading** of iframe content
- **Cache management** to prevent stale data
- **Sandboxed iframes** for security
- **Refresh controls** for each panel

## Usage

### Accessing Split Screen
1. Navigate to `http://localhost:3000/split-screen`
2. Use the toolbar to switch between view modes:
   - **Split View**: Default side-by-side view
   - **Backstage**: Show only Backstage interface
   - **Temporal**: Show only Temporal interface
   - **Open in New Tab**: Launch Temporal in separate browser tab

### Toolbar Controls
- **Split View Button**: Toggle split-screen mode (desktop only)
- **Backstage Button**: Show only Backstage catalog
- **Temporal Button**: Show only Temporal workflows
- **New Tab Icon**: Open Temporal Web UI in new browser tab

### Mobile Usage
On mobile devices, the interface automatically switches to single-view mode:
- Use the toggle buttons to switch between Backstage and Temporal
- Each interface fills the entire screen for optimal mobile experience

## Configuration

### Environment Variables
```bash
# Temporal Web UI URL (default: http://localhost:8233)
TEMPORAL_WEB_URL=http://localhost:8233

# Backstage Backend URL (default: http://localhost:8081)
BACKEND_URL=http://localhost:8081
```

### Backend Configuration
Add to your `app-config.yaml`:
```yaml
temporal:
  webUrl: ${TEMPORAL_WEB_URL}
  backendUrl: ${BACKEND_URL}
```

## Technical Implementation

### Component Structure
```
src/components/
├── SplitScreenPage.tsx          # Main split-screen component
└── SplitScreenLandingPage.tsx   # Enhanced landing page
```

### Key Features
- **React hooks** for state management and responsive behavior
- **Material-UI** components for consistent styling
- **iframe integration** for embedding external interfaces
- **Responsive breakpoints** for mobile/tablet/desktop layouts

### Security Considerations
- **Sandboxed iframes** with restricted permissions
- **CORS handling** for cross-origin communication
- **Content Security Policy** compliance

## Troubleshooting

### Common Issues

#### Temporal UI Not Loading
1. Verify Temporal Web UI is running on port 8233
2. Check network connectivity between services
3. Refresh the split-screen page

#### Mobile View Issues
1. Ensure responsive meta tags are set
2. Test with different mobile device sizes
3. Check browser console for layout warnings

#### Performance Issues
1. Clear browser cache and reload
2. Check network latency for both services
3. Monitor iframe loading times

### Development Tips
- Use browser dev tools to test responsive behavior
- Monitor console for iframe communication errors
- Test with different screen sizes during development

## Future Enhancements

### Planned Features
- **Draggable divider** to resize panels
- **Keyboard shortcuts** for quick navigation
- **Session persistence** to remember preferred view mode
- **Advanced integration** with cross-frame communication
- **Multi-workspace support** for different environments

### Integration Opportunities
- **Shared context** between Backstage and Temporal
- **Unified search** across both interfaces
- **Workflow templates** directly from Backstage catalog
- **Real-time notifications** in both panels

## Support

For issues or feature requests:
1. Check the troubleshooting section above
2. Review browser console for error messages
3. Verify all services are running correctly
4. Test with different browsers if needed
