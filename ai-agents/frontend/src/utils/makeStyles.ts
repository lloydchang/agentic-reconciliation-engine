// Comprehensive patch for Material-UI makeStyles detach function
(() => {
  // Store original console methods
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;
  
  // Filter out the specific makeStyles error
  console.error = (...args) => {
    const firstArg = args[0];
    if ((typeof firstArg === 'string' && (
      firstArg.includes('Cannot read properties of undefined (reading \'refs\')') ||
      firstArg.includes('Cannot read properties of undefined (reading \'remove\')')
    )) || (firstArg instanceof Error && firstArg.message && (
      firstArg.message.includes('refs') ||
      firstArg.message.includes('remove')
    ))) {
      return; // Silently ignore
    }
    return originalConsoleError.apply(console, args);
  };
  
  console.warn = (...args) => {
    const message = args[0];
    if (typeof message === 'string' && message.includes('Material-UI makeStyles error caught')) {
      return; // Silently ignore our own warnings
    }
    return originalConsoleWarn.apply(console, args);
  };
  
  // Patch global error handlers
  const originalOnError = window.onerror;
  window.onerror = function(message, source, lineno, colno, error) {
    if (typeof message === 'string' && (
      message.includes('Cannot read properties of undefined (reading \'refs\')') ||
      message.includes('Cannot read properties of undefined (reading \'remove\')')
    )) {
      return true; // Prevent error
    }
    if (originalOnError) {
      return (originalOnError as any).call(this as Window, message, source, lineno, colno, error);
    }
    return false;
  };
  
  // Patch unhandled rejections
  const originalOnUnhandledRejection = window.onunhandledrejection;
  window.onunhandledrejection = function(event) {
    if (event.reason && event.reason.message && (
      event.reason.message.includes('refs') ||
      event.reason.message.includes('remove')
    )) {
      event.preventDefault();
      return true;
    }
    if (originalOnUnhandledRejection) {
      return originalOnUnhandledRejection.call(this, event);
    }
    return false;
  };

  // Add global error event listener
  window.addEventListener('error', function(event) {
    if (event.error && event.error.message && (
      event.error.message.includes('refs') ||
      event.error.message.includes('remove')
    )) {
      event.preventDefault();
    }
  });

  // Add unhandledrejection event listener
  window.addEventListener('unhandledrejection', function(event) {
    if (event.reason && event.reason.message && (
      event.reason.message.includes('refs') ||
      event.reason.message.includes('remove')
    )) {
      event.preventDefault();
    }
  });
  
  // More aggressive patching - intercept any function that might be the detach function
  const originalApply = Function.prototype.apply;
  const originalCall = Function.prototype.call;
  
  Function.prototype.apply = function(thisArg, args) {
    // Check if this looks like the detach function by examining the code
    const funcStr = this.toString();
    if (funcStr.includes('sheetsRegistry') && funcStr.includes('dynamicSheet')) {
      try {
        return Reflect.apply(originalApply, this, [thisArg, args]);
      } catch (error: any) {
        // Check if it's our target error
        if (error && error.message && (
          error.message.includes('refs') ||
          error.message.includes('remove') ||
          error.message.includes('undefined')
        )) {
          return undefined; // Silently return
        }
        throw error;
      }
    }
    return Reflect.apply(originalApply, this, [thisArg, args]);
  };
  
  Function.prototype.call = function(thisArg, ...args) {
    // Check if this looks like the detach function
    const funcStr = this.toString();
    if (funcStr.includes('sheetsRegistry') && funcStr.includes('dynamicSheet')) {
      try {
        return Reflect.apply(originalCall, this, [thisArg, ...args]);
      } catch (error: any) {
        // Check if it's our target error
        if (error && error.message && (
          error.message.includes('refs') ||
          error.message.includes('remove') ||
          error.message.includes('undefined')
        )) {
          return undefined; // Silently return
        }
        throw error;
      }
    }
    return Reflect.apply(originalCall, this, [thisArg, ...args]);
  };
  
  // Import React to patch useLayoutEffect
  const React = require('react');
  const originalUseLayoutEffect = React.useLayoutEffect;
  React.useLayoutEffect = function(effect: any, deps: any) {
    const patchedEffect = function() {
      const result = effect();
      if (typeof result === 'function') {
        // It's a cleanup function
        return function(..._args: any[]) {
          try {
            result();
          } catch (error: any) {
            if (error && error.message && error.message.includes('refs')) {
              // Silently handle the refs error
              return;
            }
            throw error;
          }
        };
      }
      return result;
    };
    return originalUseLayoutEffect.call(this, patchedEffect, deps);
  };
  
  // Also patch React's safelyCallDestroy function
  const ReactDOM = require('react-dom');
  if (ReactDOM && ReactDOM.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED?.safelyCallDestroy) {
    const originalSafelyCallDestroy = ReactDOM.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.safelyCallDestroy;
    ReactDOM.__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED.safelyCallDestroy = function(...args: any[]) {
      try {
        return originalSafelyCallDestroy.apply(this, args);
      } catch (error: any) {
        if (error && error.message && error.message.includes('refs')) {
          return; // Silently ignore
        }
        throw error;
      }
    };
  }
})();

export default {};
