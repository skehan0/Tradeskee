# Testing Guide

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run specific test file
pytest tests/unit/test_config.py

# Run specific test
pytest tests/unit/test_config.py::test_settings_loads_successfully

# Run with verbose output
pytest -v

# Run with print statements shown
pytest -s
```

## Test Organization

```
tests/
├── conftest.py           # Shared fixtures (auto-discovered by pytest)
├── unit/                 # Fast, isolated tests (< 0.1s each)
│   └── test_config.py   # Test configuration
├── integration/          # Slower tests with multiple components
│   └── test_api_endpoints.py
└── fixtures/            # Mock data and responses
```

## Writing Good Tests

### 1. Test One Thing
```python
# Bad - tests multiple things
def test_config():
    settings = Settings()
    assert settings.APP_NAME == "Tradeskee"
    assert settings.PORT == 8000
    assert settings.DEBUG is False

# Good - each test has single purpose
def test_default_app_name():
    settings = Settings()
    assert settings.APP_NAME == "Tradeskee"

def test_default_port():
    settings = Settings()
    assert settings.PORT == 8000
```

### 2. Use Descriptive Names
```python
# Bad
def test_config():
    ...

# Good
def test_settings_loads_successfully():
    ...
```

### 3. Use Fixtures for Reusable Setup
```python
# In conftest.py
@pytest.fixture
def test_client():
    return TestClient(app)

# In your test
def test_health(test_client):  # <-- pytest injects fixture
    response = test_client.get("/health")
    assert response.status_code == 200
```

## Test Coverage Goals

- **Unit tests**: 80%+ coverage
- **Integration tests**: Cover critical paths
- **Overall**: 70%+ coverage minimum

## Current Test Count

Run `pytest --collect-only` to see all tests.
