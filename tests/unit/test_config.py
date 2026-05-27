"""
Unit tests for configuration management.

These tests ensure your config loads correctly, validates inputs,
and provides the right defaults.

Learning concepts demonstrated:
- Basic assertions
- Testing with invalid inputs
- Property testing
- Parametrized tests
"""
import pytest
import os
from pydantic import ValidationError
from src.core.config import Settings, get_settings


class TestSettingsBasics:
    """Basic settings loading and defaults."""
    
    def test_settings_loads_successfully(self):
        """Test that settings can be loaded without errors."""
        settings = Settings()
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_default_app_name(self):
        """Test default application name is set correctly."""
        settings = Settings()
        assert settings.APP_NAME == "Tradeskee"
    
    def test_default_environment_is_development(self):
        """Test default environment is development."""
        settings = Settings()
        assert settings.ENVIRONMENT == "development"
    
    def test_debug_from_environment(self):
        """Test debug mode is loaded from environment."""
        # Settings() loads from .env file
        settings = Settings()
        # Check it's a boolean (value depends on .env)
        assert isinstance(settings.DEBUG, bool)
    
    def test_debug_can_be_set(self):
        """Test debug mode can be explicitly set."""
        settings_debug_on = Settings(DEBUG=True)
        assert settings_debug_on.DEBUG is True
        
        settings_debug_off = Settings(DEBUG=False)
        assert settings_debug_off.DEBUG is False
    
    def test_default_port_is_8000(self):
        """Test default port is 8000."""
        settings = Settings()
        assert settings.PORT == 8000


class TestSettingsValidation:
    """Test settings validation rules."""
    
    def test_invalid_environment_raises_error(self):
        """Test that invalid environment value raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(ENVIRONMENT="invalid_env")
        
        # Check the error message contains expected text
        assert "ENVIRONMENT must be one of" in str(exc_info.value)
    
    def test_valid_environments_accepted(self):
        """Test all valid environment values are accepted."""
        valid_envs = ["development", "staging", "production"]
        
        for env in valid_envs:
            settings = Settings(ENVIRONMENT=env)
            assert settings.ENVIRONMENT == env
    
    def test_log_level_converted_to_uppercase(self):
        """Test LOG_LEVEL is automatically converted to uppercase."""
        settings = Settings(LOG_LEVEL="info")
        assert settings.LOG_LEVEL == "INFO"
        
        settings = Settings(LOG_LEVEL="DEBUG")
        assert settings.LOG_LEVEL == "DEBUG"
    
    def test_invalid_log_level_raises_error(self):
        """Test invalid log level raises ValidationError."""
        with pytest.raises(ValidationError):
            Settings(LOG_LEVEL="INVALID")


class TestCORSConfiguration:
    """Test CORS configuration parsing."""
    
    def test_cors_origins_as_list(self):
        """Test CORS origins can be provided as a list."""
        origins = ["http://localhost:3000", "http://localhost:3001"]
        settings = Settings(BACKEND_CORS_ORIGINS=origins)
        assert settings.BACKEND_CORS_ORIGINS == origins
    
    def test_cors_origins_as_comma_separated_string(self):
        """Test CORS origins can be provided as comma-separated string."""
        origins_str = "http://localhost:3000,http://localhost:3001"
        settings = Settings(BACKEND_CORS_ORIGINS=origins_str)
        
        expected = ["http://localhost:3000", "http://localhost:3001"]
        assert settings.BACKEND_CORS_ORIGINS == expected
    
    def test_cors_origins_strips_whitespace(self):
        """Test CORS parser strips whitespace from origins."""
        origins_str = "http://localhost:3000 , http://localhost:3001 "
        settings = Settings(BACKEND_CORS_ORIGINS=origins_str)
        
        # Should strip spaces around commas
        assert settings.BACKEND_CORS_ORIGINS == [
            "http://localhost:3000",
            "http://localhost:3001"
        ]


class TestSettingsProperties:
    """Test computed properties on Settings."""
    
    def test_is_development_property(self):
        """Test is_development property returns correct value."""
        dev_settings = Settings(ENVIRONMENT="development")
        assert dev_settings.is_development is True
        
        prod_settings = Settings(ENVIRONMENT="production")
        assert prod_settings.is_development is False
    
    def test_is_production_property(self):
        """Test is_production property returns correct value."""
        prod_settings = Settings(ENVIRONMENT="production")
        assert prod_settings.is_production is True
        
        dev_settings = Settings(ENVIRONMENT="development")
        assert dev_settings.is_production is False
    
    def test_database_url_property(self):
        """Test database_url property combines URL and DB name."""
        settings = Settings(
            MONGODB_URL="mongodb://localhost:27017",
            MONGODB_DB_NAME="test_db"
        )
        assert settings.database_url == "mongodb://localhost:27017/test_db"


class TestSettingsCaching:
    """Test settings caching with lru_cache."""
    
    def test_get_settings_returns_same_instance(self):
        """Test that get_settings() returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Same object in memory (singleton pattern)
        assert settings1 is settings2
        assert id(settings1) == id(settings2)


# 🎓 LEARNING EXERCISE: Parametrized Tests
# This is a more advanced pattern - same test, multiple inputs

@pytest.mark.parametrize("port,expected", [
    (8000, 8000),
    (9000, 9000),
    (3000, 3000),
])
def test_port_configuration(port, expected):
    """
    Test port can be configured to different values.
    
    This is called "parametrized testing" - runs the same test
    with different inputs. More efficient than writing separate tests.
    """
    settings = Settings(PORT=port)
    assert settings.PORT == expected


@pytest.mark.parametrize("env,is_prod", [
    ("production", True),
    ("development", False),
    ("staging", False),
])
def test_environment_production_check(env, is_prod):
    """Test is_production for different environments."""
    settings = Settings(ENVIRONMENT=env)
    assert settings.is_production == is_prod
