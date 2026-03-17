import { chromium, Browser, Page } from 'playwright';
import { execSync } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

// Configuration
const LANGFUSE_NAMESPACE = 'langfuse';
const LANGFUSE_PORT = 3010;
const DEFAULT_EMAIL = 'admin@langfuse.local';
const DEFAULT_PASSWORD = 'langfuse-admin-2024';

interface LangfuseKeys {
  publicKey: string;
  secretKey: string;
  projectId: string;
}

class LangfuseAutomator {
  private browser: Browser | null = null;
  private page: Page | null = null;

  async init(): Promise<void> {
    console.log('🚀 Initializing Playwright automation...');
    
    // Check prerequisites
    this.checkPrerequisites();
    
    // Wait for Langfuse to be ready
    await this.waitForLangfuse();
    
    // Setup port forward
    await this.setupPortForward();
    
    // Launch browser
    this.browser = await chromium.launch({ 
      headless: false, // Show browser for debugging
      slowMo: 100 // Slow down for reliability
    });
    
    this.page = await this.browser.newPage();
    
    console.log('✅ Playwright automation initialized');
  }

  private checkPrerequisites(): void {
    console.log('🔍 Checking prerequisites...');
    
    // Check kubectl
    try {
      execSync('kubectl version --client', { stdio: 'ignore' });
    } catch (error) {
      throw new Error('kubectl not found. Please install kubectl first.');
    }
    
    // Check cluster access
    try {
      execSync('kubectl cluster-info', { stdio: 'ignore' });
    } catch (error) {
      throw new Error('Cannot access Kubernetes cluster. Please check your kubeconfig.');
    }
    
    console.log('✅ Prerequisites checked');
  }

  private async waitForLangfuse(): Promise<void> {
    console.log('⏳ Waiting for Langfuse to be ready...');
    
    const maxAttempts = 60;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      try {
        const result = execSync('kubectl get pods -n langfuse -l app=langfuse --no-headers', { encoding: 'utf8' });
        if (result.includes('1/1') && result.includes('Running')) {
          console.log('✅ Langfuse is ready');
          return;
        }
      } catch (error) {
        // Continue trying
      }
      
      console.log(`Attempt ${attempt}/${maxAttempts}: Waiting for Langfuse...`);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    throw new Error('Langfuse not ready after maximum attempts');
  }

  private async setupPortForward(): Promise<void> {
    console.log('🔧 Setting up port forward...');
    
    // Kill any existing port-forward
    try {
      execSync('pkill -f "kubectl.*port-forward.*3010"', { stdio: 'ignore' });
    } catch (error) {
      // Continue if no process found
    }
    
    // Start new port-forward
    const portForwardCommand = `kubectl port-forward svc/langfuse-server ${LANGFUSE_PORT}:3000 -n ${LANGFUSE_NAMESPACE}`;
    execSync(portForwardCommand, { detached: true, stdio: 'ignore' });
    
    // Wait for port-forward to be ready
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Test connection
    const response = await fetch(`http://localhost:${LANGFUSE_PORT}/api/health`);
    if (response.ok) {
      console.log('✅ Port forward established');
    } else {
      throw new Error('Port forward failed');
    }
  }

  async createAdminAccount(): Promise<void> {
    console.log('👤 Creating admin account...');
    
    if (!this.page) throw new Error('Page not initialized');
    
    // Navigate to Langfuse
    await this.page.goto(`http://localhost:${LANGFUSE_PORT}`);
    await this.page.waitForLoadState('networkidle');
    
    // Check if signup is needed
    try {
      // Look for signup form
      const signupButton = await this.page.locator('button[type="submit"], button:has-text("Sign up")').first();
      
      if (await signupButton.isVisible()) {
        // Fill signup form
        await this.page.fill('input[name="email"], input[type="email"]', DEFAULT_EMAIL);
        await this.page.fill('input[name="password"], input[type="password"]', DEFAULT_PASSWORD);
        await this.page.fill('input[name="name"], input[placeholder*="name"]', 'Langfuse Admin');
        
        // Submit signup
        await signupButton.click();
        await this.page.waitForLoadState('networkidle');
        
        console.log('✅ Admin account created');
      } else {
        console.log('ℹ️ Admin account already exists');
      }
    } catch (error) {
      console.log('ℹ️ Checking if login is needed instead...');
      
      // Try to login if signup not available
      await this.login();
    }
  }

  private async login(): Promise<void> {
    if (!this.page) throw new Error('Page not initialized');
    
    // Navigate to login page
    await this.page.goto(`http://localhost:${LANGFUSE_PORT}/signin`);
    await this.page.waitForLoadState('networkidle');
    
    // Fill login form
    await this.page.fill('input[name="email"], input[type="email"]', DEFAULT_EMAIL);
    await this.page.fill('input[name="password"], input[type="password"]', DEFAULT_PASSWORD);
    
    // Submit login
    await this.page.click('button[type="submit"]');
    await this.page.waitForLoadState('networkidle');
    
    console.log('✅ Logged in successfully');
  }

  async createApiKeys(): Promise<LangfuseKeys> {
    console.log('🔑 Creating API keys...');
    
    if (!this.page) throw new Error('Page not initialized');
    
    // Navigate to settings
    await this.page.goto(`http://localhost:${LANGFUSE_PORT}/settings`);
    await this.page.waitForLoadState('networkidle');
    
    // Look for API keys section
    try {
      // Try to find API keys tab/button
      const apiKeysTab = await this.page.locator('button:has-text("API Keys"), a:has-text("API Keys")').first();
      await apiKeysTab.click();
      await this.page.waitForLoadState('networkidle');
    } catch (error) {
      // Alternative: navigate directly to API keys URL
      await this.page.goto(`http://localhost:${LANGFUSE_PORT}/settings/api-keys`);
      await this.page.waitForLoadState('networkidle');
    }
    
    // Create new API key
    try {
      const createButton = await this.page.locator('button:has-text("Create"), button:has-text("New Key"), button:has-text("Generate")').first();
      await createButton.click();
      await this.page.waitForTimeout(1000);
    } catch (error) {
      console.log('Could not find create button, trying alternative...');
    }
    
    // Fill key creation form
    try {
      await this.page.fill('input[name="name"], input[placeholder*="name"]', 'gitops-temporal-keys');
      await this.page.fill('textarea[name="note"], textarea[placeholder*="note"]', 'Auto-generated keys for GitOps Temporal integration');
      
      // Submit form
      const submitButton = await this.page.locator('button[type="submit"], button:has-text("Create"), button:has-text("Generate")').first();
      await submitButton.click();
      await this.page.waitForLoadState('networkidle');
    } catch (error) {
      console.log('Form filling failed, trying to extract existing keys...');
    }
    
    // Extract API keys
    const keys = await this.extractApiKeys();
    
    console.log('✅ API keys created/extracted');
    return keys;
  }

  private async extractApiKeys(): Promise<LangfuseKeys> {
    if (!this.page) throw new Error('Page not initialized');
    
    // Look for API keys on the page
    try {
      // Method 1: Look for code blocks containing keys
      const keyElements = await this.page.locator('code, pre, .api-key, .secret-key').all();
      
      let publicKey = '';
      let secretKey = '';
      
      for (const element of keyElements) {
        const text = await element.textContent();
        if (text?.startsWith('pk-lf-')) {
          publicKey = text.trim();
        } else if (text?.startsWith('sk-lf-')) {
          secretKey = text.trim();
        }
      }
      
      // Method 2: Look for clipboard copy buttons
      if (!publicKey || !secretKey) {
        const copyButtons = await this.page.locator('button:has-text("Copy"), button[aria-label*="copy"]').all();
        
        for (const button of copyButtons) {
          await button.click();
          // Try to read from clipboard (may not work due to security)
          await this.page.waitForTimeout(500);
        }
      }
      
      // Method 3: Check network requests
      if (!publicKey || !secretKey) {
        // Listen for network responses
        const keysPromise = this.page.waitForResponse(response => 
          response.url().includes('/api/projects') && response.url().includes('/keys')
        );
        
        // Try to trigger a key refresh or creation
        await this.page.reload();
        await this.page.waitForLoadState('networkidle');
        
        const response = await Promise.race([keysPromise, new Promise(resolve => setTimeout(resolve, 5000))]);
        
        if (response && 'json' in response) {
          const data = await (response as any).json();
          publicKey = data.publicKey || '';
          secretKey = data.secretKey || '';
        }
      }
      
      if (!publicKey || !secretKey) {
        throw new Error('Could not extract API keys from page');
      }
      
      return {
        publicKey,
        secretKey,
        projectId: 'gitops-infra-control-plane' // Default project ID
      };
      
    } catch (error) {
      console.error('Failed to extract API keys:', error);
      throw error;
    }
  }

  async updateKubernetesSecrets(keys: LangfuseKeys): Promise<void> {
    console.log('🔧 Updating Kubernetes secrets...');
    
    // Create namespace if it doesn't exist
    try {
      execSync('kubectl create namespace observability --dry-run=client -o yaml | kubectl apply -f -');
    } catch (error) {
      // Continue if namespace exists
    }
    
    // Create secrets
    const secretYaml = `
apiVersion: v1
kind: Secret
metadata:
  name: langfuse-secrets
  namespace: observability
type: Opaque
data:
  public-key: ${Buffer.from(keys.publicKey).toString('base64')}
  secret-key: ${Buffer.from(keys.secretKey).toString('base64')}
  project-id: ${Buffer.from(keys.projectId).toString('base64')}
`;
    
    fs.writeFileSync('/tmp/langfuse-secrets.yaml', secretYaml);
    execSync('kubectl apply -f /tmp/langfuse-secrets.yaml');
    
    // Verify secrets
    execSync('kubectl get secret langfuse-secrets -n observability');
    
    console.log('✅ Kubernetes secrets updated');
  }

  async cleanup(): Promise<void> {
    console.log('🧹 Cleaning up...');
    
    // Kill port-forward
    try {
      execSync('pkill -f "kubectl.*port-forward.*3010"', { stdio: 'ignore' });
    } catch (error) {
      // Continue if no process found
    }
    
    // Clean up temporary files
    try {
      fs.unlinkSync('/tmp/langfuse-secrets.yaml');
    } catch (error) {
      // Continue if file doesn't exist
    }
    
    // Close browser
    if (this.browser) {
      await this.browser.close();
    }
    
    console.log('✅ Cleanup completed');
  }

  async run(): Promise<void> {
    try {
      await this.init();
      await this.createAdminAccount();
      const keys = await this.createApiKeys();
      await this.updateKubernetesSecrets(keys);
      
      console.log('🎉 Automated Langfuse setup completed!');
      console.log('');
      console.log('📋 Summary:');
      console.log(`- Admin account: ${DEFAULT_EMAIL}`);
      console.log(`- Project: ${keys.projectId}`);
      console.log('- Secrets created in namespace: observability');
      console.log('');
      console.log('🌐 Access Langfuse UI:');
      console.log(`kubectl port-forward svc/langfuse-server ${LANGFUSE_PORT}:3000 -n ${LANGFUSE_NAMESPACE}`);
      console.log(`Then open: http://localhost:${LANGFUSE_PORT}`);
      console.log('');
      console.log('🔑 API keys are stored in Kubernetes secret: langfuse-secrets');
      
    } catch (error) {
      console.error('❌ Automation failed:', error);
      throw error;
    } finally {
      await this.cleanup();
    }
  }
}

// Run the automation
async function main() {
  console.log('🤖 Starting Playwright-based Langfuse automation...');
  
  const automator = new LangfuseAutomator();
  await automator.run();
}

// Handle uncaught errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error);
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled rejection at:', promise, 'reason:', reason);
  process.exit(1);
});

// Run main function
main().catch(error => {
  console.error('Automation failed:', error);
  process.exit(1);
});
