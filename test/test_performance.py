"""Performance tests for ApiHubClient."""

from unittest.mock import mock_open, patch

import pytest
import requests_mock

from apihub_client.client import ApiHubClient


class TestApiHubClientPerformance:
    """Performance tests for ApiHubClient operations."""

    @pytest.fixture
    def performance_client(self):
        """Create client for performance testing."""
        return ApiHubClient(
            api_key="performance_test_key",
            base_url="https://api.performance.test",
        )

    @pytest.fixture
    def large_mock_file_content(self):
        """Create large mock file content for performance testing."""
        return b"Large PDF content for performance testing " * 10000

    def test_extract_upload_performance(
        self, performance_client, large_mock_file_content, benchmark
    ):
        """Test performance of file upload during extract operation."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.performance.test/extract/performance_test",
                json={"file_hash": "perf_hash_123", "status": "PROCESSING"},
                status_code=200,
            )

            def upload_operation():
                with patch(
                    "builtins.open", mock_open(read_data=large_mock_file_content)
                ):
                    return performance_client.extract(
                        endpoint="performance_test",
                        vertical="table",
                        sub_vertical="performance_test",
                        file_path="/test/large_file.pdf",
                    )

            result = benchmark(upload_operation)
            assert result["file_hash"] == "perf_hash_123"

    def test_polling_performance_fast_completion(
        self, performance_client, large_mock_file_content, benchmark
    ):
        """Test polling performance when processing completes quickly."""
        with requests_mock.Mocker() as m:
            # Mock extract
            m.post(
                "https://api.performance.test/extract/fast_process",
                json={"file_hash": "fast_hash_123", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock immediate completion
            m.get(
                "https://api.performance.test/status?file_hash=fast_hash_123",
                json={"status": "COMPLETED"},
                status_code=200,
            )

            # Mock retrieve
            m.get(
                "https://api.performance.test/retrieve?file_hash=fast_hash_123",
                json={"result": "fast_completion_data"},
                status_code=200,
            )

            def fast_completion_workflow():
                with patch(
                    "builtins.open", mock_open(read_data=large_mock_file_content)
                ):
                    with patch("time.sleep"):
                        return performance_client.extract(
                            endpoint="fast_process",
                            vertical="table",
                            sub_vertical="fast_process",
                            file_path="/test/file.pdf",
                            wait_for_completion=True,
                            polling_interval=0.1,
                        )

            result = benchmark(fast_completion_workflow)
            assert result["result"] == "fast_completion_data"

    def test_polling_performance_slow_completion(
        self, performance_client, large_mock_file_content, benchmark
    ):
        """Test polling performance with multiple status checks."""
        with requests_mock.Mocker() as m:
            # Mock extract
            m.post(
                "https://api.performance.test/extract/slow_process",
                json={"file_hash": "slow_hash_456", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock multiple processing status responses
            status_responses = []
            for i in range(5):  # 5 polling cycles
                status_responses.append(
                    {
                        "json": {"status": "PROCESSING", "progress": i * 20},
                        "status_code": 200,
                    }
                )
            status_responses.append(
                {"json": {"status": "COMPLETED", "progress": 100}, "status_code": 200}
            )

            for response in status_responses:
                m.get(
                    "https://api.performance.test/status?file_hash=slow_hash_456",
                    **response,
                )

            # Mock retrieve
            m.get(
                "https://api.performance.test/retrieve?file_hash=slow_hash_456",
                json={"result": "slow_completion_data"},
                status_code=200,
            )

            def slow_completion_workflow():
                with patch(
                    "builtins.open", mock_open(read_data=large_mock_file_content)
                ):
                    with patch("time.sleep"):  # Mock sleep to avoid actual delays
                        return performance_client.extract(
                            endpoint="slow_process",
                            vertical="table",
                            sub_vertical="slow_process",
                            file_path="/test/file.pdf",
                            wait_for_completion=True,
                            polling_interval=0.1,
                        )

            result = benchmark(slow_completion_workflow)
            assert result["result"] == "slow_completion_data"

    def test_multiple_sequential_requests_performance(
        self, performance_client, large_mock_file_content, benchmark
    ):
        """Test performance of multiple sequential API requests."""
        with requests_mock.Mocker() as m:
            # Mock multiple different endpoints
            endpoints = ["discover", "extract", "process", "analyze"]

            for i, endpoint in enumerate(endpoints):
                m.post(
                    f"https://api.performance.test/extract/{endpoint}",
                    json={"file_hash": f"hash_{i}", "status": "PROCESSING"},
                    status_code=200,
                )

                m.get(
                    f"https://api.performance.test/status?file_hash=hash_{i}",
                    json={"status": "COMPLETED"},
                    status_code=200,
                )

                m.get(
                    f"https://api.performance.test/retrieve?file_hash=hash_{i}",
                    json={"result": f"data_{endpoint}"},
                    status_code=200,
                )

            def sequential_requests():
                results = []
                with patch(
                    "builtins.open", mock_open(read_data=large_mock_file_content)
                ):
                    with patch("time.sleep"):
                        for endpoint in endpoints:
                            result = performance_client.extract(
                                endpoint=endpoint,
                                vertical="table",
                                sub_vertical=endpoint,
                                file_path="/test/file.pdf",
                                wait_for_completion=True,
                                polling_interval=0.1,
                            )
                            results.append(result)
                return results

            results = benchmark(sequential_requests)
            assert len(results) == 4
            for i, result in enumerate(results):
                assert result["result"] == f"data_{endpoints[i]}"

    def test_memory_usage_large_response(
        self, performance_client, large_mock_file_content, benchmark
    ):
        """Test memory efficiency with large API responses."""
        # Create a large mock response
        large_response = {
            "file_hash": "large_response_hash",
            "result": {
                "data": ["row_" + str(i) for i in range(10000)],  # Large dataset
                "metadata": {"size": "large", "processing_time": 60},
            },
        }

        with requests_mock.Mocker() as m:
            m.post(
                "https://api.performance.test/extract/large_response",
                json={"file_hash": "large_response_hash", "status": "PROCESSING"},
                status_code=200,
            )

            m.get(
                "https://api.performance.test/status?file_hash=large_response_hash",
                json={"status": "COMPLETED"},
                status_code=200,
            )

            m.get(
                "https://api.performance.test/retrieve?file_hash=large_response_hash",
                json=large_response,
                status_code=200,
            )

            def large_response_workflow():
                with patch(
                    "builtins.open", mock_open(read_data=large_mock_file_content)
                ):
                    with patch("time.sleep"):
                        return performance_client.extract(
                            endpoint="large_response",
                            vertical="table",
                            sub_vertical="large_response",
                            file_path="/test/file.pdf",
                            wait_for_completion=True,
                            polling_interval=0.1,
                        )

            result = benchmark(large_response_workflow)
            assert len(result["result"]["data"]) == 10000

    def test_api_request_overhead(self, performance_client, benchmark):
        """Test the overhead of API request setup and teardown."""
        with requests_mock.Mocker() as m:
            m.get(
                "https://api.performance.test/status?file_hash=overhead_test",
                json={"status": "COMPLETED"},
                status_code=200,
            )

            def simple_status_check():
                return performance_client.get_status("overhead_test")

            result = benchmark(simple_status_check)
            assert result["status"] == "COMPLETED"

    def test_concurrent_status_checks(self, performance_client, benchmark):
        """Test performance of rapid consecutive status checks."""
        with requests_mock.Mocker() as m:
            # Mock status endpoint
            m.get(
                "https://api.performance.test/status",
                json={"status": "PROCESSING"},
                status_code=200,
            )

            def rapid_status_checks():
                file_hashes = [f"hash_{i}" for i in range(10)]
                results = []
                for hash_id in file_hashes:
                    result = performance_client.get_status(hash_id)
                    results.append(result)
                return results

            results = benchmark(rapid_status_checks)
            assert len(results) == 10
            assert all(r["status"] == "PROCESSING" for r in results)

    @pytest.mark.parametrize("file_size_multiplier", [1, 10, 100])
    def test_file_size_impact_on_performance(
        self, performance_client, file_size_multiplier, benchmark
    ):
        """Test how file size affects upload performance."""
        file_content = b"Content " * (1000 * file_size_multiplier)

        with requests_mock.Mocker() as m:
            m.post(
                "https://api.performance.test/extract/size_test",
                json={"file_hash": f"size_hash_{file_size_multiplier}"},
                status_code=200,
            )

            def upload_sized_file():
                with patch("builtins.open", mock_open(read_data=file_content)):
                    return performance_client.extract(
                        endpoint="size_test",
                        vertical="table",
                        sub_vertical="size_test",
                        file_path="/test/sized_file.pdf",
                    )

            result = benchmark(upload_sized_file)
            assert result["file_hash"] == f"size_hash_{file_size_multiplier}"

    def test_error_handling_performance(self, performance_client, benchmark):
        """Test performance impact of error handling."""
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.performance.test/extract/error_test",
                text="Internal Server Error",
                status_code=500,
            )

            def error_handling_operation():
                try:
                    with patch("builtins.open", mock_open(read_data=b"test")):
                        performance_client.extract(
                            endpoint="error_test",
                            vertical="table",
                            sub_vertical="error_test",
                            file_path="/test/file.pdf",
                        )
                except Exception:
                    return "error_handled"

            result = benchmark(error_handling_operation)
            assert result == "error_handled"
