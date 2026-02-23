from src.core.config import settings

def test_config_loads_from_env():
    assert settings.APP_NAME == "Tradeskee API"
    assert settings.ENVIRONMENT == "test"
    assert settings.DEBUG is True
    
def test_config_validation_fails_on_invalid_env():
    """Test that invalid environment raises a validation error."""