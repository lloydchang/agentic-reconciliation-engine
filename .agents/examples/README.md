# Agent Skills Configuration Examples

This directory contains configuration templates and examples for the multi-cloud agent skills.

## 📁 Files

- `config.template.json` - Configuration template with placeholders
- `config.example.json` - Example with realistic values (safe to share)

## 🚀 Quick Setup

### 1. Copy the Template

```bash
cp config.template.json config.json
```

### 2. Update with Your Values

Edit `config.json` and replace the placeholder values:

- `YOUR_AWS_ACCOUNT_ID` → Your actual AWS account ID
- `YOUR_AZURE_SUBSCRIPTION_ID` → Your Azure subscription ID
- `/path/to/your/kubeconfig` → Path to your kubeconfig file
- Other credentials and endpoints

### 3. Set Up Environment Variables

```bash
export AWS_PROFILE=default
export AZURE_SUBSCRIPTION_ID=your-subscription-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
export KUBECONFIG=/path/to/kubeconfig
```

## 🔐 Security Best Practices

### Never Commit Real Configurations

- ✅ Use templates with placeholders
- ✅ Keep real configs in `.gitignore`
- ✅ Use environment variables for sensitive data
- ✅ Rotate credentials regularly

### Recommended File Structure

```
.agents/
├── examples/
│   ├── config.template.json  # ✅ Template (committed)
│   ├── config.example.json   # ✅ Safe example (committed)
│   └── README.md             # ✅ Documentation (committed)
└── config.json               # ❌ Real config (gitignored)
```

## 🏢 Environment-Specific Configs

Create separate configs for different environments:

```bash
# Development
cp config.template.json config.dev.json

# Staging  
cp config.template.json config.staging.json

# Production
cp config.template.json config.prod.json
```

Use environment-specific configs:

```bash
python main.py provision --config config.dev.json
python main.py provision --config config.prod.json
```

## 🔧 Configuration Options

### Provider Settings

Each cloud provider section includes:

- `enabled`: Whether to use this provider
- `region`: Default region for operations
- `credentials`: Authentication configuration

### Orchestration Settings

- `max_workers`: Maximum concurrent operations
- `timeout_minutes`: Operation timeout
- `retry_attempts`: Number of retry attempts

### Monitoring Settings

- Prometheus, Grafana, AlertManager endpoints
- Metrics collection configuration
- Alert thresholds

### Security Settings

- Encryption requirements
- Audit logging configuration
- Production approval requirements

## 📋 Configuration Validation

The agent skills validate configurations on startup:

```bash
# Validate configuration
python main.py validate-config --config config.json

# Check provider connectivity
python main.py test-connectivity --config config.json
```

## 🚨 Common Issues

### Missing Credentials

```
Error: AWS credentials not found
Solution: Configure AWS CLI or set environment variables
```

### Invalid Region

```
Error: Invalid region 'invalid-region'
Solution: Use valid region codes (us-west-2, eastus, us-central1)
```

### Network Connectivity

```
Error: Cannot connect to Prometheus
Solution: Check network connectivity and endpoint URLs
```

## 📞 Support

For configuration issues:

1. Check the template for required fields
2. Validate JSON syntax: `python -m json.tool config.json`
3. Test connectivity with CLI tools
4. Review logs with `--verbose` flag

---

**Remember**: Never commit real credentials or configurations to version control!
