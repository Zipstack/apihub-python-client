"""Integration tests for ApiHubClient full workflow scenarios."""

import os
import tempfile
from unittest.mock import patch

import pytest
import requests_mock

from apihub_client.client import ApiHubClient, ApiHubClientException


class TestApiHubClientIntegration:
    """Integration tests for complete workflow scenarios."""

    @pytest.fixture
    def integration_client(self):
        """Create client for integration testing."""
        return ApiHubClient(
            api_key="integration_test_key",
            base_url="https://api.integration.test",
        )

    @pytest.fixture
    def sample_pdf_file(self):
        """Create a temporary PDF file for integration testing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4 Mock PDF content for integration testing")
            temp_path = f.name

        yield temp_path

        # Cleanup
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass

    def test_full_discover_extract_workflow(self, integration_client, sample_pdf_file):
        """Test complete discover -> extract workflow."""
        with requests_mock.Mocker() as m:
            # Step 1: Discover tables
            m.post(
                "https://api.integration.test/extract/discover_tables",
                json={
                    "file_hash": "discover_hash_123",
                    "status": "PROCESSING",
                    "message": "Discovery started",
                },
                status_code=200,
            )

            # Mock status responses for discover
            m.get(
                "https://api.integration.test/status?file_hash=discover_hash_123",
                [
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "COMPLETED"}, "status_code": 200},
                ],
            )

            # Mock retrieve response for discover
            m.get(
                "https://api.integration.test/retrieve?file_hash=discover_hash_123",
                json={
                    "file_hash": "discover_hash_123",
                    "status": "COMPLETED",
                    "result": {
                        "tables_found": 2,
                        "tables": [
                            {"table_number": 1, "location": {"page": 1, "bbox": []}},
                            {"table_number": 2, "location": {"page": 2, "bbox": []}},
                        ],
                    },
                },
                status_code=200,
            )

            # Step 2: Extract specific table
            m.post(
                "https://api.integration.test/extract/extract_table",
                json={
                    "file_hash": "extract_hash_456",
                    "status": "PROCESSING",
                    "message": "Table extraction started",
                },
                status_code=200,
            )

            # Mock status responses for extract
            m.get(
                "https://api.integration.test/status?file_hash=extract_hash_456",
                [
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "COMPLETED"}, "status_code": 200},
                ],
            )

            # Mock retrieve response for extract
            m.get(
                "https://api.integration.test/retrieve?file_hash=extract_hash_456",
                json={
                    "file_hash": "extract_hash_456",
                    "status": "COMPLETED",
                    "result": {
                        "table_data": [
                            ["Header 1", "Header 2", "Header 3"],
                            ["Row 1 Col 1", "Row 1 Col 2", "Row 1 Col 3"],
                            ["Row 2 Col 1", "Row 2 Col 2", "Row 2 Col 3"],
                        ],
                        "metadata": {"table_number": 1, "confidence": 0.95},
                    },
                },
                status_code=200,
            )

            # Execute the workflow
            # Step 1: Discover tables with wait_for_completion
            with patch("time.sleep"):
                discover_result = integration_client.extract(
                    endpoint="discover_tables",
                    vertical="table",
                    sub_vertical="discover_tables",
                    file_path=sample_pdf_file,
                    wait_for_completion=True,
                    polling_interval=1,
                )

            # Verify discover results
            assert discover_result["result"]["tables_found"] == 2
            assert len(discover_result["result"]["tables"]) == 2

            # Step 2: Extract specific table using cached file
            with patch("time.sleep"):
                extract_result = integration_client.extract(
                    endpoint="extract_table",
                    vertical="table",
                    sub_vertical="extract_table",
                    file_hash="discover_hash_123",  # Use original file hash
                    ext_table_no=1,
                    wait_for_completion=True,
                    polling_interval=1,
                )

            # Verify extract results
            assert len(extract_result["result"]["table_data"]) == 3
            assert extract_result["result"]["metadata"]["table_number"] == 1
            assert extract_result["result"]["metadata"]["confidence"] == 0.95

    def test_bank_statement_processing_workflow(
        self, integration_client, sample_pdf_file
    ):
        """Test bank statement processing with wait_for_completion."""
        with requests_mock.Mocker() as m:
            # Mock bank statement processing
            m.post(
                "https://api.integration.test/extract/bank_statement",
                json={
                    "file_hash": "bank_hash_789",
                    "status": "PROCESSING",
                    "estimated_time": 30,
                },
                status_code=200,
            )

            # Mock status progression
            status_progression = [
                {"status": "PROCESSING", "progress": 25},
                {"status": "PROCESSING", "progress": 50},
                {"status": "PROCESSING", "progress": 75},
                {"status": "COMPLETED", "progress": 100},
            ]

            for status_data in status_progression:
                m.get(
                    "https://api.integration.test/status?file_hash=bank_hash_789",
                    json=status_data,
                    status_code=200,
                )

            # Mock final result
            m.get(
                "https://api.integration.test/retrieve?file_hash=bank_hash_789",
                json={
                    "file_hash": "bank_hash_789",
                    "status": "COMPLETED",
                    "result": {
                        "account_info": {
                            "account_number": "****1234",
                            "bank_name": "Test Bank",
                            "statement_period": "Jan 2024",
                        },
                        "transactions": [
                            {
                                "date": "2024-01-15",
                                "description": "ATM Withdrawal",
                                "amount": -100.00,
                                "balance": 1500.00,
                            },
                            {
                                "date": "2024-01-16",
                                "description": "Direct Deposit",
                                "amount": 2000.00,
                                "balance": 3500.00,
                            },
                        ],
                        "summary": {
                            "starting_balance": 1600.00,
                            "ending_balance": 3500.00,
                            "total_deposits": 2000.00,
                            "total_withdrawals": 100.00,
                        },
                    },
                },
                status_code=200,
            )

            # Execute bank statement processing
            with patch("time.sleep"):
                result = integration_client.extract(
                    endpoint="bank_statement",
                    vertical="table",
                    sub_vertical="bank_statement",
                    file_path=sample_pdf_file,
                    wait_for_completion=True,
                    polling_interval=2,
                )

            # Verify results
            assert result["result"]["account_info"]["account_number"] == "****1234"
            assert len(result["result"]["transactions"]) == 2
            assert result["result"]["summary"]["ending_balance"] == 3500.00

    def test_manual_workflow_without_wait_for_completion(
        self, integration_client, sample_pdf_file
    ):
        """Test manual workflow: extract -> status -> retrieve."""
        with requests_mock.Mocker() as m:
            # Mock extract response
            m.post(
                "https://api.integration.test/extract/invoice",
                json={
                    "file_hash": "invoice_hash_abc",
                    "status": "PROCESSING",
                    "queue_position": 3,
                },
                status_code=200,
            )

            # Mock status check
            m.get(
                "https://api.integration.test/status?file_hash=invoice_hash_abc",
                json={"status": "COMPLETED", "processing_time": 45},
                status_code=200,
            )

            # Mock retrieve response
            m.get(
                "https://api.integration.test/retrieve?file_hash=invoice_hash_abc",
                json={
                    "file_hash": "invoice_hash_abc",
                    "status": "COMPLETED",
                    "result": {
                        "invoice_data": {
                            "invoice_number": "INV-2024-001",
                            "date": "2024-01-15",
                            "vendor": "Test Vendor Inc.",
                            "total_amount": 1250.75,
                            "line_items": [
                                {"description": "Service A", "amount": 1000.00},
                                {"description": "Service B", "amount": 250.75},
                            ],
                        }
                    },
                },
                status_code=200,
            )

            # Step 1: Extract (without wait_for_completion)
            extract_result = integration_client.extract(
                endpoint="invoice",
                vertical="form",
                sub_vertical="invoice",
                file_path=sample_pdf_file,
                wait_for_completion=False,  # Explicit false
            )

            assert extract_result["file_hash"] == "invoice_hash_abc"
            assert extract_result["status"] == "PROCESSING"

            # Step 2: Check status manually
            status_result = integration_client.get_status("invoice_hash_abc")
            assert status_result["status"] == "COMPLETED"

            # Step 3: Retrieve results manually
            final_result = integration_client.retrieve("invoice_hash_abc")
            assert (
                final_result["result"]["invoice_data"]["invoice_number"]
                == "INV-2024-001"
            )
            assert final_result["result"]["invoice_data"]["total_amount"] == 1250.75

    def test_error_handling_in_workflow(self, integration_client, sample_pdf_file):
        """Test error handling throughout the workflow."""
        with requests_mock.Mocker() as m:
            # Test 1: Extract failure
            m.post(
                "https://api.integration.test/extract/invalid_endpoint",
                text="Endpoint not found",
                status_code=404,
            )

            with pytest.raises(ApiHubClientException) as exc_info:
                integration_client.extract(
                    endpoint="invalid_endpoint",
                    vertical="table",
                    sub_vertical="invalid",
                    file_path=sample_pdf_file,
                )

            assert exc_info.value.status_code == 404

            # Test 2: Status check failure
            m.get(
                "https://api.integration.test/status?file_hash=nonexistent_hash",
                text="File hash not found",
                status_code=404,
            )

            with pytest.raises(ApiHubClientException):
                integration_client.get_status("nonexistent_hash")

            # Test 3: Retrieve failure
            m.get(
                "https://api.integration.test/retrieve?file_hash=expired_hash",
                text="File expired",
                status_code=410,
            )

            with pytest.raises(ApiHubClientException):
                integration_client.retrieve("expired_hash")

    def test_processing_failure_with_wait_for_completion(
        self, integration_client, sample_pdf_file
    ):
        """Test processing failure during wait_for_completion."""
        with requests_mock.Mocker() as m:
            # Mock successful extract
            m.post(
                "https://api.integration.test/extract/failing_process",
                json={"file_hash": "fail_hash_xyz", "status": "PROCESSING"},
                status_code=200,
            )

            # Mock status progression ending in failure
            m.get(
                "https://api.integration.test/status?file_hash=fail_hash_xyz",
                [
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {"json": {"status": "PROCESSING"}, "status_code": 200},
                    {
                        "json": {
                            "status": "FAILED",
                            "error": "Invalid file format detected",
                        },
                        "status_code": 200,
                    },
                ],
            )

            with patch("time.sleep"):
                with pytest.raises(ApiHubClientException) as exc_info:
                    integration_client.extract(
                        endpoint="failing_process",
                        vertical="table",
                        sub_vertical="test",
                        file_path=sample_pdf_file,
                        wait_for_completion=True,
                    )

            assert "Processing failed for file_hash: fail_hash_xyz" in str(
                exc_info.value
            )

    def test_concurrent_processing_simulation(
        self, integration_client, sample_pdf_file
    ):
        """Test handling multiple concurrent processing requests."""
        with requests_mock.Mocker() as m:
            # Mock multiple file processing
            files_data = [
                ("file1_hash", "discover_tables"),
                ("file2_hash", "bank_statement"),
                ("file3_hash", "invoice"),
            ]

            for file_hash, endpoint in files_data:
                # Mock extract
                m.post(
                    f"https://api.integration.test/extract/{endpoint}",
                    json={"file_hash": file_hash, "status": "PROCESSING"},
                    status_code=200,
                )

                # Mock status and retrieve
                m.get(
                    f"https://api.integration.test/status?file_hash={file_hash}",
                    json={"status": "COMPLETED"},
                    status_code=200,
                )

                m.get(
                    f"https://api.integration.test/retrieve?file_hash={file_hash}",
                    json={
                        "file_hash": file_hash,
                        "result": {"data": f"processed_{endpoint}"},
                    },
                    status_code=200,
                )

            results = []
            # Simulate concurrent processing
            for file_hash, endpoint in files_data:
                with patch("time.sleep"):
                    result = integration_client.extract(
                        endpoint=endpoint,
                        vertical="table" if endpoint != "invoice" else "form",
                        sub_vertical=endpoint,
                        file_path=sample_pdf_file,
                        wait_for_completion=True,
                        polling_interval=0.1,
                    )
                    results.append((file_hash, result))

            # Verify all processing completed successfully
            assert len(results) == 3
            for file_hash, result in results:
                assert result["file_hash"] == file_hash
                assert "processed_" in result["result"]["data"]

    def test_large_file_processing_timeout_handling(self, integration_client):
        """Test handling of large files with extended processing times."""
        with requests_mock.Mocker() as m:
            # Create a larger temporary file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                f.write(b"%PDF-1.4 " + b"Large PDF content " * 1000)
                large_file_path = f.name

            try:
                # Mock extract for large file
                m.post(
                    "https://api.integration.test/extract/large_document",
                    json={
                        "file_hash": "large_file_hash",
                        "status": "PROCESSING",
                        "estimated_time": 120,
                    },
                    status_code=200,
                )

                # Mock extended processing time
                long_processing_responses = []
                for i in range(10):  # Simulate 10 status checks
                    long_processing_responses.append(
                        {
                            "json": {"status": "PROCESSING", "progress": i * 10},
                            "status_code": 200,
                        }
                    )

                long_processing_responses.append(
                    {
                        "json": {"status": "COMPLETED", "progress": 100},
                        "status_code": 200,
                    }
                )

                for response in long_processing_responses:
                    m.get(
                        "https://api.integration.test/status?file_hash=large_file_hash",
                        **response,
                    )

                # Mock final retrieve
                m.get(
                    "https://api.integration.test/retrieve?file_hash=large_file_hash",
                    json={
                        "file_hash": "large_file_hash",
                        "result": {"processed_pages": 50, "extraction_quality": "high"},
                    },
                    status_code=200,
                )

                # Process with shorter polling interval for testing
                with patch("time.sleep"):
                    result = integration_client.extract(
                        endpoint="large_document",
                        vertical="table",
                        sub_vertical="large_document",
                        file_path=large_file_path,
                        wait_for_completion=True,
                        polling_interval=0.1,  # Fast polling for test
                    )

                assert result["result"]["processed_pages"] == 50
                assert result["result"]["extraction_quality"] == "high"

            finally:
                # Cleanup
                try:
                    os.unlink(large_file_path)
                except FileNotFoundError:
                    pass
