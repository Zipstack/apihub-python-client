"""Comprehensive test cases for ApiHubClient."""

import time
from unittest.mock import mock_open, patch

import pytest
import requests_mock
from apihub_client.client import ApiHubClient, ApiHubClientException


class TestApiHubClientException:
    """Test cases for ApiHubClientException."""

    def test_exception_with_message_only(self):
        """Test exception creation with message only."""
        exception = ApiHubClientException("Test error")
        assert exception.message == "Test error"
        assert exception.status_code is None
        assert str(exception) == "'Message: Test error, Status Code: None'"

    def test_exception_with_message_and_status_code(self):
        """Test exception creation with message and status code."""
        exception = ApiHubClientException("Test error", 400)
        assert exception.message == "Test error"
        assert exception.status_code == 400
        assert str(exception) == "'Message: Test error, Status Code: 400'"


class TestApiHubClient:
    """Test cases for ApiHubClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return ApiHubClient(api_key="test_api_key", base_url="https://api.test.com")

    @pytest.fixture
    def mock_file_content(self):
        """Mock file content for testing."""
        return b"test file content"

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test_api_key"
        assert client.base_url == "https://api.test.com"
        assert client.headers == {"apikey": "test_api_key"}

    def test_extract_with_file_path_success(self, client, mock_file_content):
        """Test extract method with file path."""
        with requests_mock.Mocker() as m:
            # Mock successful response
            m.post(
                "https://api.test.com/extract/discover_tables",
                json={"file_hash": "test_hash_123", "status": "PROCESSING"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.extract(
                    endpoint="discover_tables",
                    vertical="table",
                    sub_vertical="discover_tables",
                    file_path="/test/file.pdf",
                    ext_cache_result="true",
                )

            assert result["file_hash"] == "test_hash_123"
            assert result["status"] == "PROCESSING"

            # Verify request details
            assert len(m.request_history) == 1
            request = m.request_history[0]
            assert (
                request.url
                == "https://api.test.com/extract/discover_tables?vertical=table&sub_vertical=discover_tables&ext_cache_result=true"
            )
            assert request.headers["apikey"] == "test_api_key"

    def test_extract_with_file_hash_success(self, client):
        """Test extract method with file hash."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/extract/extract_table",
                json={"file_hash": "test_hash_456", "status": "PROCESSING"},
                status_code=200,
            )

            result = client.extract(
                endpoint="extract_table",
                vertical="table",
                sub_vertical="extract_table",
                file_hash="existing_hash",
                ext_table_no=1,
            )

            assert result["file_hash"] == "test_hash_456"

            # Verify request details
            request = m.request_history[0]
            assert "use_cached_file_hash=existing_hash" in request.url
            assert "ext_table_no=1" in request.url

    def test_extract_failure(self, client):
        """Test extract method with API failure."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/extract/test_endpoint",
                text="Internal Server Error",
                status_code=500,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                client.extract(
                    endpoint="test_endpoint",
                    vertical="table",
                    sub_vertical="test",
                )

            assert exc_info.value.message == "Internal Server Error"
            assert exc_info.value.status_code == 500

    def test_extract_with_wait_for_completion_success(self, client, mock_file_content):
        """Test extract method with wait_for_completion=True."""
        with requests_mock.Mocker() as m:
            # Mock extract response
            m.post(
                "https://api.test.com/extract/bank_statement",
                json={"file_hash": "test_hash_789", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock status responses (first PROCESSING, then COMPLETED)
            m.get(
                "https://api.test.com/status?file_hash=test_hash_789",
                [
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "COMPLETED"}, "status_code": 200},
                ],
            )

            # Mock retrieve response
            m.get(
                "https://api.test.com/retrieve?file_hash=test_hash_789",
                json={
                    "file_hash": "test_hash_789",
                    "status": "COMPLETED",
                    "result": {"extracted_data": "test_data"},
                },
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with patch("time.sleep") as mock_sleep:
                    result = client.extract(
                        endpoint="bank_statement",
                        vertical="table",
                        sub_vertical="bank_statement",
                        file_path="/test/bank.pdf",
                        wait_for_completion=True,
                        polling_interval=1,
                    )

            # Verify final result
            assert result["result"]["extracted_data"] == "test_data"
            assert result["status"] == "COMPLETED"

            # Verify sleep was called with correct interval
            assert mock_sleep.call_count >= 1
            mock_sleep.assert_called_with(1)

    def test_extract_with_wait_for_completion_failed_status(
        self, client, mock_file_content
    ):
        """Test extract method with wait_for_completion when processing fails."""
        with requests_mock.Mocker() as m:
            # Mock extract response
            m.post(
                "https://api.test.com/extract/bank_statement",
                json={"file_hash": "test_hash_fail", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock status response with FAILED status
            m.get(
                "https://api.test.com/status?file_hash=test_hash_fail",
                json={"status": "FAILED"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with patch("time.sleep"):
                    with pytest.raises(ApiHubClientException) as exc_info:
                        client.extract(
                            endpoint="bank_statement",
                            vertical="table",
                            sub_vertical="bank_statement",
                            file_path="/test/bank.pdf",
                            wait_for_completion=True,
                        )

            assert (
                "Processing failed for file_hash: test_hash_fail"
                in exc_info.value.message
            )

    def test_extract_with_wait_for_completion_no_file_hash(
        self, client, mock_file_content
    ):
        """Test extract method with wait_for_completion when no file_hash."""
        with requests_mock.Mocker() as m:
            # Mock extract response without file_hash
            m.post(
                "https://api.test.com/extract/test_endpoint",
                json={"status": "PROCESSING"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.extract(
                    endpoint="test_endpoint",
                    vertical="table",
                    sub_vertical="test",
                    file_path="/test/file.pdf",
                    wait_for_completion=True,
                )

            # Should return the initial response without polling
            assert result["status"] == "PROCESSING"
            assert "file_hash" not in result

    def test_get_status_success(self, client):
        """Test get_status method success."""
        with requests_mock.Mocker() as m:
            m.get(
                "https://api.test.com/status?file_hash=test_hash",
                json={"status": "COMPLETED", "file_hash": "test_hash"},
                status_code=200,
            )

            result = client.get_status("test_hash")

            assert result["status"] == "COMPLETED"
            assert result["file_hash"] == "test_hash"

    def test_get_status_failure(self, client):
        """Test get_status method with API failure."""
        with requests_mock.Mocker() as m:
            m.get(
                "https://api.test.com/status?file_hash=test_hash",
                text="Not Found",
                status_code=404,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                client.get_status("test_hash")

            assert exc_info.value.message == "Not Found"
            assert exc_info.value.status_code == 404

    def test_retrieve_success(self, client):
        """Test retrieve method success."""
        with requests_mock.Mocker() as m:
            expected_result = {
                "file_hash": "test_hash",
                "status": "COMPLETED",
                "result": {"extracted_data": "sample_data", "metadata": {"pages": 2}},
            }

            m.get(
                "https://api.test.com/retrieve?file_hash=test_hash",
                json=expected_result,
                status_code=200,
            )

            result = client.retrieve("test_hash")

            assert result == expected_result
            assert result["result"]["extracted_data"] == "sample_data"

    def test_retrieve_failure(self, client):
        """Test retrieve method with API failure."""
        with requests_mock.Mocker() as m:
            m.get(
                "https://api.test.com/retrieve?file_hash=test_hash",
                text="Service Unavailable",
                status_code=503,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                client.retrieve("test_hash")

            assert exc_info.value.message == "Service Unavailable"
            assert exc_info.value.status_code == 503

    def test_extract_file_upload_error(self, client):
        """Test extract method when file cannot be opened."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(FileNotFoundError):
                client.extract(
                    endpoint="test_endpoint",
                    vertical="table",
                    sub_vertical="test",
                    file_path="/nonexistent/file.pdf",
                )

    def test_extract_with_additional_kwargs(self, client, mock_file_content):
        """Test extract method with additional keyword arguments."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/extract/custom_endpoint",
                json={"file_hash": "test_hash_custom"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                client.extract(
                    endpoint="custom_endpoint",
                    vertical="table",
                    sub_vertical="custom",
                    file_path="/test/file.pdf",
                    custom_param="custom_value",
                    another_param=123,
                )

            # Verify additional parameters were included
            request = m.request_history[0]
            assert "custom_param=custom_value" in request.url
            assert "another_param=123" in request.url

    def test_logging_output(self, client, caplog, mock_file_content):
        """Test that appropriate logging messages are generated."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.test.com/extract/test_endpoint",
                json={"file_hash": "test_hash_log"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with caplog.at_level("INFO"):
                    client.extract(
                        endpoint="test_endpoint",
                        vertical="table",
                        sub_vertical="test",
                        file_path="/test/file.pdf",
                    )

            # Check for expected log messages
            log_messages = [record.message for record in caplog.records]
            assert any("Uploading file to extract" in msg for msg in log_messages)
            assert any(
                "Operation completed successfully" in msg for msg in log_messages
            )

    @pytest.mark.parametrize(
        "endpoint,vertical,sub_vertical",
        [
            ("discover_tables", "table", "discover_tables"),
            ("extract_table", "table", "extract_table"),
            ("bank_statement", "table", "bank_statement"),
            ("invoice", "form", "invoice"),
        ],
    )
    def test_extract_different_endpoints(
        self, client, endpoint, vertical, sub_vertical, mock_file_content
    ):
        """Test extract method with different endpoint configurations."""
        with requests_mock.Mocker() as m:
            m.post(
                f"https://api.test.com/extract/{endpoint}",
                json={"file_hash": f"hash_{endpoint}"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.extract(
                    endpoint=endpoint,
                    vertical=vertical,
                    sub_vertical=sub_vertical,
                    file_path="/test/file.pdf",
                )

            assert result["file_hash"] == f"hash_{endpoint}"

    def test_extract_real_polling_timing(self, client, mock_file_content):
        """Test that polling respects the specified interval."""
        with requests_mock.Mocker() as m:
            # Mock extract response
            m.post(
                "https://api.test.com/extract/bank_statement",
                json={"file_hash": "timing_test_hash"},
                status_code=200,
            )

            # Mock status responses
            m.get(
                "https://api.test.com/status?file_hash=timing_test_hash",
                [
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "COMPLETED"}, "status_code": 200},
                ],
            )

            # Mock retrieve response
            m.get(
                "https://api.test.com/retrieve?file_hash=timing_test_hash",
                json={"result": "final_data"},
                status_code=200,
            )

            start_time = time.time()

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.extract(
                    endpoint="bank_statement",
                    vertical="table",
                    sub_vertical="bank_statement",
                    file_path="/test/bank.pdf",
                    wait_for_completion=True,
                    polling_interval=0.1,  # Very short interval for testing
                )

            end_time = time.time()

            # Should have completed quickly due to short polling interval
            assert (end_time - start_time) < 2.0  # Should complete within 2 seconds
            assert result["result"] == "final_data"

    def test_wait_for_complete_standalone_success(self, client):
        """Test wait_for_complete method called standalone."""
        with requests_mock.Mocker() as m:
            # Mock status responses (first PROCESSING, then COMPLETED)
            m.get(
                "https://api.test.com/status?file_hash=standalone_hash",
                [
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "COMPLETED"}, "status_code": 200},
                ],
            )

            # Mock retrieve response
            m.get(
                "https://api.test.com/retrieve?file_hash=standalone_hash",
                json={
                    "file_hash": "standalone_hash",
                    "status": "COMPLETED",
                    "result": {"data": "standalone_result"},
                },
                status_code=200,
            )

            with patch("time.sleep") as mock_sleep:
                result = client.wait_for_complete(
                    "standalone_hash", timeout=300, polling_interval=2
                )

            assert result["status"] == "COMPLETED"
            assert result["result"]["data"] == "standalone_result"
            mock_sleep.assert_called_with(2)

    def test_wait_for_complete_timeout_exception(self, client):
        """Test wait_for_complete method timeout exception."""
        with requests_mock.Mocker() as m:
            # Mock status responses that never complete
            m.get(
                "https://api.test.com/status?file_hash=timeout_hash",
                json={"status": "PROCESSING"},
                status_code=200,
            )

            with patch("time.sleep"):
                # Use return_value instead of side_effect for timeout simulation
                with patch("time.time") as mock_time:
                    # First call returns 0, subsequent calls return 601 (timeout)
                    mock_time.side_effect = [0, 601]
                    with pytest.raises(ApiHubClientException) as exc_info:
                        client.wait_for_complete("timeout_hash", timeout=600)

            assert "Timeout waiting for completion" in exc_info.value.message
            assert "timeout_hash" in exc_info.value.message
            assert exc_info.value.status_code is None

    def test_client_initialization_with_trailing_slash(self):
        """Test client initialization removes trailing slash from base_url."""
        client = ApiHubClient(api_key="test_key", base_url="https://api.test.com/")
        assert client.base_url == "https://api.test.com"
        assert client.api_key == "test_key"
        assert client.headers == {"apikey": "test_key"}
