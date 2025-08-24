"""Comprehensive test cases for DocSplitterClient."""

import time
from unittest.mock import mock_open, patch

import pytest
import requests_mock
from apihub_client.client import ApiHubClientException
from apihub_client.doc_splitter import DocSplitterClient


class TestDocSplitterClient:
    """Test cases for DocSplitterClient."""

    @pytest.fixture
    def client(self):
        """Create a test client instance."""
        return DocSplitterClient(
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

    def test_upload_success(self, client, mock_file_content):
        """Test successful file upload."""
        with requests_mock.Mocker() as m:
            # Mock successful upload response
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={"job_id": "test-job-123", "status": "PROCESSING"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.upload(file_path="/test/document.pdf")

            assert result["job_id"] == "test-job-123"
            assert result["status"] == "PROCESSING"

            # Verify request details
            assert len(m.request_history) == 1
            request = m.request_history[0]
            assert (
                request.url
                == "http://localhost:8005/api/v1/doc-splitter/documents/upload"
            )
            assert request.headers["apikey"] == "test_api_key"

    def test_upload_success_202_nested_response(self, client, mock_file_content):
        """Test successful file upload with 202 status and nested response."""
        with requests_mock.Mocker() as m:
            # Mock successful upload response with 202 and nested data structure
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={
                    "data": {
                        "filename": "test.pdf",
                        "job_id": "93bbb7ab-3291-429c-8923-3b179e7ae5bf",
                        "pages": 2,
                        "size_bytes": 63580,
                        "status": "queued",
                        "upload_timestamp": "2025-08-23T04:28:32.424535Z",
                        "user_limits": {
                            "current_jobs": 1,
                            "jobs_today": 3,
                            "max_jobs_per_day": 5000,
                            "max_parallel_jobs": 5,
                        },
                    },
                    "request_id": "eb75ac1e-a224-4624-a4f2-6c813ddc2b3c",
                    "success": True,
                    "timestamp": "2025-08-23T04:28:32.424612",
                },
                status_code=202,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.upload(file_path="/test/document.pdf")

            # Verify we got the nested response structure
            assert result["data"]["job_id"] == "93bbb7ab-3291-429c-8923-3b179e7ae5bf"
            assert result["data"]["status"] == "queued"
            assert result["success"] is True

    def test_upload_file_not_found(self, client):
        """Test upload with non-existent file."""
        with patch("builtins.open", side_effect=FileNotFoundError("File not found")):
            with pytest.raises(ApiHubClientException) as exc_info:
                client.upload(file_path="/nonexistent/file.pdf")

            assert "File not found: /nonexistent/file.pdf" in exc_info.value.message

    def test_upload_failure(self, client, mock_file_content):
        """Test upload with API failure."""
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                text="Bad Request",
                status_code=400,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with pytest.raises(ApiHubClientException) as exc_info:
                    client.upload(file_path="/test/document.pdf")

            assert exc_info.value.message == "Bad Request"
            assert exc_info.value.status_code == 400

    def test_upload_with_wait_for_completion_success(self, client, mock_file_content):
        """Test upload with wait_for_completion=True."""
        with requests_mock.Mocker() as m:
            # Mock upload response
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={"job_id": "test-job-456", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock status responses (first PROCESSING, then COMPLETED)
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job-456",
                [
                    {
                        "json": {"status": "PROCESSING", "job_id": "test-job-456"},
                        "status_code": 200,
                    },
                    {
                        "json": {"status": "PROCESSING", "job_id": "test-job-456"},
                        "status_code": 200,
                    },
                    {
                        "json": {"status": "COMPLETED", "job_id": "test-job-456"},
                        "status_code": 200,
                    },
                ],
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with patch("time.sleep") as mock_sleep:
                    result = client.upload(
                        file_path="/test/document.pdf",
                        wait_for_completion=True,
                        polling_interval=1,
                    )

            # Verify final result
            assert result["status"] == "COMPLETED"
            assert result["job_id"] == "test-job-456"

            # Verify sleep was called with correct interval
            assert mock_sleep.call_count >= 1
            mock_sleep.assert_called_with(1)

    def test_upload_with_wait_for_completion_failed_status(
        self, client, mock_file_content
    ):
        """Test upload with wait_for_completion when processing fails."""
        with requests_mock.Mocker() as m:
            # Mock upload response
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={"job_id": "test-job-fail", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock status response with FAILED status
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job-fail",
                json={"status": "FAILED", "job_id": "test-job-fail"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with patch("time.sleep"):
                    with pytest.raises(ApiHubClientException) as exc_info:
                        client.upload(
                            file_path="/test/document.pdf",
                            wait_for_completion=True,
                        )

            assert (
                "Processing failed for job_id: test-job-fail" in exc_info.value.message
            )

    def test_upload_with_wait_for_completion_no_job_id(self, client, mock_file_content):
        """Test upload with wait_for_completion when no job_id in response."""
        with requests_mock.Mocker() as m:
            # Mock upload response without job_id
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={"status": "PROCESSING"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.upload(
                    file_path="/test/document.pdf",
                    wait_for_completion=True,
                )

            # Should return the initial response without polling
            assert result["status"] == "PROCESSING"
            assert "job_id" not in result

    def test_get_job_status_success(self, client):
        """Test get_job_status method success."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job",
                json={"status": "COMPLETED", "job_id": "test-job"},
                status_code=200,
            )

            result = client.get_job_status("test-job")

            assert result["status"] == "COMPLETED"
            assert result["job_id"] == "test-job"

    def test_get_job_status_failure(self, client):
        """Test get_job_status method with API failure."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job",
                text="Not Found",
                status_code=404,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                client.get_job_status("test-job")

            assert exc_info.value.message == "Not Found"
            assert exc_info.value.status_code == 404

    def test_download_result_success(self, client, tmp_path):
        """Test download_result method success."""
        # Create a temporary output path
        output_path = tmp_path / "result.zip"

        mock_file_content = b"mock zip file content"

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/download?job_id=test-job",
                content=mock_file_content,
                status_code=200,
            )

            result_path = client.download_result("test-job", str(output_path))

            # Verify file was written correctly
            assert result_path == str(output_path)
            assert output_path.exists()
            assert output_path.read_bytes() == mock_file_content

    def test_download_result_default_filename(self, client):
        """Test download_result with default filename."""
        mock_file_content = b"mock zip file content"

        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/download?job_id=test-job-123",
                content=mock_file_content,
                status_code=200,
            )

            with patch("builtins.open", mock_open()) as mock_file:
                result_path = client.download_result("test-job-123")

            assert result_path == "result_test-job-123.zip"
            mock_file.assert_called_once_with("result_test-job-123.zip", "wb")

    def test_download_result_failure(self, client):
        """Test download_result method with API failure."""
        with requests_mock.Mocker() as m:
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/download?job_id=test-job",
                text="Service Unavailable",
                status_code=503,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                client.download_result("test-job", "output.zip")

            assert exc_info.value.message == "Service Unavailable"
            assert exc_info.value.status_code == 503

    def test_wait_for_completion_success(self, client):
        """Test wait_for_completion method success."""
        with requests_mock.Mocker() as m:
            # Mock status responses (first PROCESSING, then COMPLETED)
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job",
                [
                    {
                        "json": {"status": "PROCESSING", "job_id": "test-job"},
                        "status_code": 200,
                    },
                    {
                        "json": {"status": "COMPLETED", "job_id": "test-job"},
                        "status_code": 200,
                    },
                ],
            )

            with patch("time.sleep") as mock_sleep:
                result = client.wait_for_completion("test-job", polling_interval=1)

            assert result["status"] == "COMPLETED"
            assert result["job_id"] == "test-job"
            mock_sleep.assert_called_with(1)

    def test_wait_for_completion_timeout(self, client):
        """Test wait_for_completion with timeout."""
        with requests_mock.Mocker() as m:
            # Mock status responses that never complete
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job",
                json={"status": "PROCESSING", "job_id": "test-job"},
                status_code=200,
            )

            with patch("time.sleep"):
                with pytest.raises(ApiHubClientException) as exc_info:
                    client.wait_for_completion(
                        "test-job", timeout=1, polling_interval=0.1
                    )

            assert "Timeout waiting for completion" in exc_info.value.message
            assert "test-job" in exc_info.value.message

    def test_wait_for_completion_failed_status(self, client):
        """Test wait_for_completion with failed job."""
        with requests_mock.Mocker() as m:
            # Mock status response with FAILED status
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-job",
                json={"status": "FAILED", "job_id": "test-job"},
                status_code=200,
            )

            with patch("time.sleep"):
                with pytest.raises(ApiHubClientException) as exc_info:
                    client.wait_for_completion("test-job")

            assert "Processing failed for job_id: test-job" in exc_info.value.message

    def test_wait_for_completion_nested_response(self, client):
        """Test wait_for_completion with nested response structure."""
        with requests_mock.Mocker() as m:
            # Mock status responses with nested structure (processing, then completed)
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=test-nested",
                [
                    {
                        "json": {
                            "data": {
                                "status": "processing",
                                "job_id": "test-nested",
                                "current_step": "page_image_gen",
                            },
                            "success": True,
                        },
                        "status_code": 200,
                    },
                    {
                        "json": {
                            "data": {
                                "status": "completed",
                                "job_id": "test-nested",
                                "finished_at": "2025-08-23T04:40:00.000000Z",
                            },
                            "success": True,
                        },
                        "status_code": 200,
                    },
                ],
            )

            with patch("time.sleep") as mock_sleep:
                result = client.wait_for_completion("test-nested", polling_interval=1)

            # Should successfully complete and return the nested structure
            assert result["data"]["status"] == "completed"
            assert result["data"]["job_id"] == "test-nested"
            assert result["success"] is True
            mock_sleep.assert_called_with(1)

    def test_logging_output(self, client, caplog, mock_file_content):
        """Test that appropriate logging messages are generated."""
        with requests_mock.Mocker() as m:
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={"job_id": "test-job-log"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                with caplog.at_level("INFO"):
                    client.upload(file_path="/test/document.pdf")

            # Check for expected log messages
            log_messages = [record.message for record in caplog.records]
            assert any("Uploading file for splitting" in msg for msg in log_messages)
            assert any("Upload completed successfully" in msg for msg in log_messages)

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
        client = DocSplitterClient(api_key="test", base_url=base_url)

        # Base URL should be normalized (trailing slash removed)
        expected_base = base_url.rstrip("/")
        assert client.base_url == expected_base

        with requests_mock.Mocker() as m:
            expected_url = f"{expected_base}/api/v1/doc-splitter/documents/upload"
            m.post(
                expected_url,
                json={"job_id": "test-job"},
                status_code=200,
            )

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.upload(file_path="/test/document.pdf")

            assert result["job_id"] == "test-job"

    def test_upload_real_timing(self, client, mock_file_content):
        """Test that polling respects the specified interval."""
        with requests_mock.Mocker() as m:
            # Mock upload response
            m.post(
                "http://localhost:8005/api/v1/doc-splitter/documents/upload",
                json={"job_id": "timing-test"},
                status_code=200,
            )

            # Mock status responses
            m.get(
                "http://localhost:8005/api/v1/doc-splitter/jobs/status?job_id=timing-test",
                [
                    {
                        "json": {"status": "PROCESSING", "job_id": "timing-test"},
                        "status_code": 200,
                    },
                    {
                        "json": {"status": "COMPLETED", "job_id": "timing-test"},
                        "status_code": 200,
                    },
                ],
            )

            start_time = time.time()

            with patch("builtins.open", mock_open(read_data=mock_file_content)):
                result = client.upload(
                    file_path="/test/document.pdf",
                    wait_for_completion=True,
                    polling_interval=0.1,  # Very short interval for testing
                )

            end_time = time.time()

            # Should have completed quickly due to short polling interval
            assert (end_time - start_time) < 2.0  # Should complete within 2 seconds
            assert result["status"] == "COMPLETED"
