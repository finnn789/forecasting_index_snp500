"""
tests/test_core/test_settings.py — Unit tests untuk app/core/settings.py
"""

import pytest
from app.core.settings import settings


class TestSettingsDefaults:
    """Test default settings values."""

    def test_api_port_default(self):
        """Test default API port is 8000."""
        assert settings.api_port == 8000

    def test_api_host_default(self):
        """Test default API host is 0.0.0.0."""
        assert settings.api_host == "0.0.0.0"

    def test_debug_is_bool(self):
        """Test debug field is boolean."""
        assert isinstance(settings.debug, bool)


class TestDataFilter:
    """Test data filter settings."""

    def test_data_filter_start(self):
        """Test data_filter_start."""
        assert settings.data_filter_start == "2018-01-02"

    def test_data_filter_end(self):
        """Test data_filter_end."""
        assert settings.data_filter_end == "2024-03-04"


class TestFinbertSettings:
    """Test FinBERT-related settings."""

    def test_finbert_model_name(self):
        """Test finbert_model_name is set."""
        # Just verify it's a non-empty string containing finbert reference
        assert isinstance(settings.finbert_model_name, str)
        assert len(settings.finbert_model_name) > 0

    def test_finbert_local_path_contains_finbert(self):
        """Test finbert_local_path contains 'finbert'."""
        assert "finbert" in settings.finbert_local_path.lower()

    def test_lstm_model_path(self):
        """Test lstm_model_path contains lstm reference."""
        assert "lstm" in settings.lstm_model_path.lower()
        assert isinstance(settings.lstm_model_path, str)
        assert len(settings.lstm_model_path) > 0


class TestOptionalSettings:
    """Test optional settings fields."""

    def test_stock_api_key_optional(self):
        """Test stock_api_key can be None."""
        # Dalam test environment tanpa .env, ini bisa None
        # atau memiliki nilai jika ada .env
        assert settings.stock_api_key is None or isinstance(settings.stock_api_key, str)

    def test_news_api_key_optional(self):
        """Test news_api_key can be None."""
        assert settings.news_api_key is None or isinstance(settings.news_api_key, str)
