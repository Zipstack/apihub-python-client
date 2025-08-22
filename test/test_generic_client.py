"""Comprehensive test cases for GenericUnstractClient."""

import time
from unittest.mock import mock_open, patch

import pytest
import requests_mock
from apihub_client.client import ApiHubClientException
from apihub_client.generic_client import GenericUnstractClient


class TestGenericUnstractClient:
    """Test cases for GenericUnstractClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return GenericUnstractClient(
            api_key="test_api_key", base_url="http://localhost:8005"
        )

    @pytest.fixture
    def mock_file_content(self):
        """Mock file content for testing."""
        return b"test pdf content"

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test_api_key"
        assert client.base_url == "http://localhost:8005"
        assert client.headers == {"apikey": "test_api_key"}

    def test_process_success(self, client, mock_file_content):
        """Test successful file processing."""
        with requests_mock.Mocker() as m:
            # Mock successful processing response
            m.post(
                "http://localhost:8005/api/v1/invoice",
                json={"execution_id": "test-exec-123", "status": "PROCESSING"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.process(
                    endpoint="invoice", file_path="/test/invoice.pdf"
                )

            assert result["execution_id"] == "test-exec-123"
            assert result["status"] == "PROCESSING"

            # Verify request details
            assert len(m.request_history) == 1
            request = m.request_history[0]
            assert request.url == "http://localhost:8005/api/v1/invoice"
            assert request.headers["apikey"] == "test_api_key"

    def test_process_file_not_found(self, client):
        """Test process with non-existent file."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(ApiHubClientException) as exc_info:
                client.process(endpoint="invoice", file_path="/nonexistent/file.pdf")

            assert "File not found: /nonexistent/file.pdf" in exc_info.value.message

    def test_process_failure(self, client, mock_file_content):
        """Test process with API failure."""
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8005/api/v1/invoice",
                text="Bad Request",
                status_code=400,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with pytest.raises(ApiHubClientException) as exc_info:
                    client.process(endpoint="invoice", file_path="/test/invoice.pdf")

            assert exc_info.value.message == "Bad Request"
            assert exc_info.value.status_code == 400

    def test_process_with_wait_for_completion_success(self, client, mock_file_content):
        """Test process with wait_for_completion=True."""
        with requests_mock.Mocker() as m:
            # Mock process response
            m.post(
                "http://localhost:8005/api/v1/contract",
                json={"execution_id": "test-exec-456", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock get_result responses (first PROCESSING, then COMPLETED)
            m.get(
                "http://localhost:8005/api/v1/contract?execution_id=test-exec-456",
                [
                    {
                        "json": {
                            "status": "PROCESSING",
                            "execution_id": "test-exec-456",
                        },
                        "status_code": 200,
                    },
                    {
                        "json": {
                            "status": "PROCESSING",
                            "execution_id": "test-exec-456",
                        },
                        "status_code": 200,
                    },
                    {
                        "json": {
                            "status": "COMPLETED",
                            "execution_id": "test-exec-456",
                            "result": {"extracted_data": "contract_data"},
                        },
                        "status_code": 200,
                    },
                ],
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with patch("time.sleep") as mock_sleep:
                    result = client.process(
                        endpoint="contract",
                        file_path="/test/contract.pdf",
                        wait_for_completion=True,
                        polling_interval=1,
                    )

            # Verify final result
            assert result["status"] == "COMPLETED"
            assert result["execution_id"] == "test-exec-456"
            assert result["result"]["extracted_data"] == "contract_data"

            # Verify sleep was called with correct interval
            assert mock_sleep.call_count >= 1
            mock_sleep.assert_called_with(1)

    def test_process_with_wait_for_completion_failed_status(
        self, client, mock_file_content
    ):
        """Test process with wait_for_completion when processing fails."""
        with requests_mock.Mocker() as m:
            # Mock process response
            m.post(
                "http://localhost:8005/api/v1/invoice",
                json={"execution_id": "test-exec-fail", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock get_result response with FAILED status
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=test-exec-fail",
                json={
                    "status": "FAILED",
                    "execution_id": "test-exec-fail",
                    "error": "Processing error occurred",
                },
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with patch("time.sleep"):
                    with pytest.raises(ApiHubClientException) as exc_info:
                        client.process(
                            endpoint="invoice",
                            file_path="/test/invoice.pdf",
                            wait_for_completion=True,
                        )

            assert (
                "Processing failed for execution_id: test-exec-fail"
                in exc_info.value.message
            )
            assert "Processing error occurred" in exc_info.value.message

    def test_process_with_wait_for_completion_no_execution_id(
        self, client, mock_file_content
    ):
        """Test process with wait_for_completion when no execution_id in response."""
        with requests_mock.Mocker() as m:
            # Mock process response without execution_id
            m.post(
                "http://localhost:8005/api/v1/invoice",
                json={"status": "PROCESSING"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.process(
                    endpoint="invoice",
                    file_path="/test/invoice.pdf",
                    wait_for_completion=True,
                )

            # Should return the initial response without polling
            assert result["status"] == "PROCESSING"
            assert "execution_id" not in result

    def test_get_result_success(self, client):
        """Test get_result method success."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/receipt?execution_id=test-exec",
                json={
                    "status": "COMPLETED",
                    "execution_id": "test-exec",
                    "result": {"total_amount": 123.45},
                },
                status_code=200,
            )

            result = client.get_result("receipt", "test-exec")

            assert result["status"] == "COMPLETED"
            assert result["execution_id"] == "test-exec"
            assert result["result"]["total_amount"] == 123.45

    def test_get_result_failure(self, client):
        """Test get_result method with API failure."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                text="Not Found",
                status_code=404,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                client.get_result("invoice", "test-exec")

            assert exc_info.value.message == "Not Found"
            assert exc_info.value.status_code == 404

    def test_wait_for_completion_success(self, client):
        """Test wait_for_completion method success."""
        with requests_mock.Mocker() as m:
            # Mock get_result responses (first PROCESSING, then COMPLETED)
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                [
                    {
                        "json": {"status": "PROCESSING", "execution_id": "test-exec"},
                        "status_code": 200,
                    },
                    {
                        "json": {
                            "status": "COMPLETED",
                            "execution_id": "test-exec",
                            "result": {"data": "final_result"},
                        },
                        "status_code": 200,
                    },
                ],
            )

            with patch("time.sleep") as mock_sleep:
                result = client.wait_for_completion(
                    "invoice", "test-exec", polling_interval=1
                )

            assert result["status"] == "COMPLETED"
            assert result["execution_id"] == "test-exec"
            assert result["result"]["data"] == "final_result"
            mock_sleep.assert_called_with(1)

    def test_wait_for_completion_timeout(self, client):
        """Test wait_for_completion with timeout."""
        with requests_mock.Mocker() as m:
            # Mock get_result responses that never complete
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                json={"status": "PROCESSING", "execution_id": "test-exec"},
                status_code=200,
            )

            with patch("time.sleep"):
                with pytest.raises(ApiHubClientException) as exc_info:
                    client.wait_for_completion(
                        "invoice", "test-exec", timeout=1, polling_interval=0.1
                    )

            assert "Timeout waiting for completion" in exc_info.value.message
            assert "test-exec" in exc_info.value.message

    def test_wait_for_completion_failed_status(self, client):
        """Test wait_for_completion with failed processing."""
        with requests_mock.Mocker() as m:
            # Mock get_result response with FAILED status
            m.get(
                "http://localhost:8005/api/v1/contract?execution_id=test-exec",
                json={
                    "status": "ERROR",
                    "execution_id": "test-exec",
                    "error": "Validation failed",
                },
                status_code=200,
            )

            with patch("time.sleep"):
                with pytest.raises(ApiHubClientException) as exc_info:
                    client.wait_for_completion("contract", "test-exec")

            assert (
                "Processing failed for execution_id: test-exec"
                in exc_info.value.message
            )
            assert "Validation failed" in exc_info.value.message

    def test_check_status_success(self, client):
        """Test check_status method success."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                json={"status": "IN_PROGRESS", "execution_id": "test-exec"},
                status_code=200,
            )

            status = client.check_status("invoice", "test-exec")
            assert status == "IN_PROGRESS"

    def test_check_status_failure(self, client):
        """Test check_status method with API failure."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                text="Internal Server Error",
                status_code=500,
            )

            with pytest.raises(ApiHubClientException):
                client.check_status("invoice", "test-exec")

    def test_logging_output(self, client, caplog, mock_file_content):
        """Test that appropriate logging messages are generated."""
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8005/api/v1/invoice",
                json={"execution_id": "test-exec-log"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with caplog.at_level("INFO"):
                    client.process(endpoint="invoice", file_path="/test/invoice.pdf")

            # Check for expected log messages
            log_messages = [record.message for record in caplog.records]
            assert any("Processing file with endpoint" in msg for msg in log_messages)
            assert any("Processing started successfully" in msg for msg in log_messages)

    @pytest.mark.parametrize(
        "endpoint",
        ["invoice", "contract", "receipt", "purchase_order", "bank_statement"],
    )
    def test_different_endpoints(self, client, endpoint, mock_file_content):
        """Test process method with different endpoint configurations."""
        with requests_mock.Mocker() as m:
            m.post(
                f"http://localhost:8005/api/v1/{endpoint}",
                json={"execution_id": f"exec_{endpoint}"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.process(
                    endpoint=endpoint,
                    file_path="/test/document.pdf",
                )

            assert result["execution_id"] == f"exec_{endpoint}"

    @pytest.mark.parametrize(
        "base_url",
        [
            "http://localhost:8005",
            "http://localhost:8005/",
            "https://api.example.com",
            "https://api.example.com/",
        ],
    )
    def test_different_base_urls(self, base_url, mock_file_content):
        """Test client with different base URL formats."""
        client = GenericUnstractClient(api_key="test", base_url=base_url)

        # Base URL should be normalized (trailing slash removed)
        expected_base = base_url.rstrip("/")
        assert client.base_url == expected_base

        with requests_mock.Mocker() as m:
            expected_url = f"{expected_base}/api/v1/invoice"
            m.post(
                expected_url,
                json={"execution_id": "test-exec"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.process(
                    endpoint="invoice", file_path="/test/invoice.pdf"
                )

            assert result["execution_id"] == "test-exec"

    @pytest.mark.parametrize(
        "status_value,expected_completion",
        [
            ("COMPLETED", True),
            ("SUCCESS", True),
            ("FINISHED", True),
            ("FAILED", False),
            ("ERROR", False),
            ("PROCESSING", "continue"),
            ("IN_PROGRESS", "continue"),
            ("RUNNING", "continue"),
            ("UNKNOWN_STATUS", "continue"),
        ],
    )
    def test_status_handling_in_wait_for_completion(
        self, client, status_value, expected_completion
    ):
        """Test different status values in wait_for_completion."""
        with requests_mock.Mocker() as m:
            if expected_completion is True:
                # Should complete successfully
                m.get(
                    "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                    json={
                        "status": status_value,
                        "execution_id": "test-exec",
                        "result": {"data": "completed"},
                    },
                    status_code=200,
                )

                with patch("time.sleep"):
                    result = client.wait_for_completion("invoice", "test-exec")
                    assert result["status"] == status_value

            elif expected_completion is False:
                # Should fail
                m.get(
                    "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                    json={
                        "status": status_value,
                        "execution_id": "test-exec",
                        "error": "Test error",
                    },
                    status_code=200,
                )

                with patch("time.sleep"):
                    with pytest.raises(ApiHubClientException):
                        client.wait_for_completion("invoice", "test-exec")

            else:  # expected_completion == "continue"
                # Should continue polling (we'll timeout quickly for test)
                m.get(
                    "http://localhost:8005/api/v1/invoice?execution_id=test-exec",
                    json={"status": status_value, "execution_id": "test-exec"},
                    status_code=200,
                )

                with patch("time.sleep"):
                    with pytest.raises(ApiHubClientException) as exc_info:
                        client.wait_for_completion(
                            "invoice", "test-exec", timeout=0.1, polling_interval=0.05
                        )
                    assert "Timeout waiting for completion" in exc_info.value.message

    def test_process_real_timing(self, client, mock_file_content):
        """Test that polling respects the specified interval."""
        with requests_mock.Mocker() as m:
            # Mock process response
            m.post(
                "http://localhost:8005/api/v1/invoice",
                json={"execution_id": "timing-test"},
                status_code=200,
            )

            # Mock get_result responses
            m.get(
                "http://localhost:8005/api/v1/invoice?execution_id=timing-test",
                [
                    {
                        "json": {"status": "PROCESSING", "execution_id": "timing-test"},
                        "status_code": 200,
                    },
                    {
                        "json": {
                            "status": "COMPLETED",
                            "execution_id": "timing-test",
                            "result": {"data": "final"},
                        },
                        "status_code": 200,
                    },
                ],
            )

            start_time = time.time()

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.process(
                    endpoint="invoice",
                    file_path="/test/invoice.pdf",
                    wait_for_completion=True,
                    polling_interval=0.1,  # Very short interval for testing
                )

            end_time = time.time()

            # Should have completed quickly due to short polling interval
            assert (end_time - start_time) < 2.0  # Should complete within 2 seconds
            assert result["status"] == "COMPLETED"
