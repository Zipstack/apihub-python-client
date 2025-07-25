"""Shared test fixtures and configuration for pytest."""

import os
import tempfile
from unittest.mock import Mock

import pytest


@pytest.fixture
def temp_file():
    """Create a temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as f:
        f.write(b"Test file content for API testing")
        temp_path = f.name

    yield temp_path

    # Cleanup
    try:
        os.unlink(temp_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def sample_pdf_path():
    """Return a sample PDF file path for testing."""
    return "/path/to/sample.pdf"


@pytest.fixture
def api_responses():
    """Common API response fixtures."""
    return {
        "extract_success": {
            "file_hash": "test_file_hash_123",
            "status": "PROCESSING",
            "message": "File uploaded successfully",
        },
        "status_processing": {
            "file_hash": "test_file_hash_123",
            "status": "PROCESSING",
            "progress": 50,
        },
        "status_completed": {
            "file_hash": "test_file_hash_123",
            "status": "COMPLETED",
            "progress": 100,
        },
        "status_failed": {
            "file_hash": "test_file_hash_123",
            "status": "FAILED",
            "error": "Processing failed due to invalid file format",
        },
        "retrieve_success": {
            "file_hash": "test_file_hash_123",
            "status": "COMPLETED",
            "result": {
                "extracted_data": {
                    "tables": [
                        {
                            "table_number": 1,
                            "data": [
                                ["Name", "Amount", "Date"],
                                ["Transaction 1", "$100.00", "2024-01-15"],
                                ["Transaction 2", "$250.50", "2024-01-16"],
                            ],
                        }
                    ]
                },
                "metadata": {
                    "pages": 2,
                    "processing_time": 15.3,
                    "confidence_score": 0.95,
                },
            },
        },
    }


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "API_KEY": "test_api_key_12345",
        "BASE_URL": "https://api.test.com",
        "LOG_LEVEL": "DEBUG",
        "REQUEST_TIMEOUT": "30",
        "MAX_WAIT_TIMEOUT": "300",
        "POLL_INTERVAL": "5",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env


@pytest.fixture
def client_config():
    """Default client configuration for testing."""
    return {"api_key": "test_api_key", "base_url": "https://api.test.com"}


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging functionality."""
    return Mock()


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment before each test."""
    # Ensure any existing environment variables don't interfere
    test_env_vars = ["API_KEY", "BASE_URL", "LOG_LEVEL"]
    original_values = {}

    for var in test_env_vars:
        original_values[var] = os.environ.get(var)
        if var in os.environ:
            del os.environ[var]

    yield

    # Restore original environment variables
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value


@pytest.fixture
def sample_file_content():
    """Sample file content for testing file operations."""
    return {
        "pdf": b"%PDF-1.4 sample PDF content for testing",
        "text": b"This is sample text content for testing API upload functionality.",
        "json": b'{"test": "data", "number": 123, "array": [1, 2, 3]}',
    }


@pytest.fixture
def mock_requests_session():
    """Mock requests session for testing HTTP operations."""
    session = Mock()
    session.post.return_value = Mock()
    session.get.return_value = Mock()
    return session


# Parameterized fixtures for testing different scenarios
@pytest.fixture(
    params=[
        ("discover_tables", "table", "discover_tables"),
        ("extract_table", "table", "extract_table"),
        ("bank_statement", "table", "bank_statement"),
        ("invoice", "form", "invoice"),
        ("receipt", "form", "receipt"),
    ]
)
def endpoint_configs(request):
    """Different endpoint configurations for testing."""
    endpoint, vertical, sub_vertical = request.param
    return {"endpoint": endpoint, "vertical": vertical, "sub_vertical": sub_vertical}


@pytest.fixture(params=[1, 3, 5, 10])
def polling_intervals(request):
    """Different polling intervals for testing wait_for_completion."""
    return request.param


@pytest.fixture(params=[200, 400, 401, 404, 500, 503])
def http_status_codes(request):
    """Different HTTP status codes for testing error handling."""
    return request.param
