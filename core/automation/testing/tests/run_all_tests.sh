# Agent Naming Standards Test Suite Runner

## Usage

```bash
# Run all tests
./core/automation/testing/run_all_tests.sh

# Run with coverage
./core/automation/testing/run_all_tests.sh --coverage

# Quick validation
./core/automation/testing/run_all_tests.sh --quick
```

## Test Categories

- **Unit Tests**: Individual function testing
- **Integration Tests**: End-to-end workflow testing
- **Regression Tests**: Prevent previous issues from reoccurring

## Dependencies

- `../core/core/automation/ci-cd/scripts/ensure-agent-naming-standards.sh` - Main automation script
- Test fixtures in `core/automation/testing/fixtures/`
- Bash 4.0+ for modern parameter handling

## Output Formats

- **Console**: Colored output for immediate feedback
- **JUnit**: XML format for CI/CD integration
- **JSON**: Machine-readable results for automation
- **HTML**: Coverage reports with detailed breakdown

## Continuous Integration

Integrate with your CI/CD pipeline:
```yaml
- name: Run Agent Naming Tests
  run: ./core/automation/testing/run_all_tests.sh --coverage
```
