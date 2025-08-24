import logging
import time
from urllib.parse import parse_qs, urlparse

import requests

from .client import ApiHubClientException


class GenericUnstractClient:
    """
    Client for interacting with generic Unstract APIs.

    Handles dynamic endpoint processing operations including file upload
    and result retrieval using execution_id tracking.
    """

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        api_key: str,
        base_url: str,
    ) -> None:
        """
        Initialize the GenericUnstractClient.

        Args:
            api_key: API key for authentication
            base_url: Base URL of the Unstract service
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"apikey": self.api_key}

    def _extract_execution_id_from_url(self, url: str) -> str | None:
        """
        Extract execution_id from a URL's query parameters.

        Args:
            url: URL containing execution_id parameter

        Returns:
            str | None: The execution_id if found, None otherwise
        """
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            execution_ids = query_params.get("execution_id")
            if execution_ids:
                return execution_ids[0]  # Get the first value
        except Exception as e:
            self.logger.warning("Failed to extract execution_id from URL: %s", e)
        return None

    def process(
        self,
        endpoint: str,
        file_path: str,
        wait_for_completion: bool = False,
        polling_interval: int = 5,
        timeout: int = 600,
    ) -> dict:
        """
        Process a document using the specified endpoint.

        Args:
            endpoint: The endpoint name (e.g., 'invoice', 'contract', 'receipt')
            file_path: Path to the file to upload
            wait_for_completion: If True, polls for completion and returns final result
            polling_interval: Seconds to wait between status checks (default: 5)
            timeout: Maximum time to wait for completion in seconds (default: 600)

        Returns:
            dict: Response containing execution_id and processing information

        Raises:
            ApiHubClientException: If upload fails
        """
        url = f"{self.base_url}/api/v1/{endpoint}"

        self.logger.info("Processing file with endpoint %s: %s", endpoint, file_path)

        try:
            with open(file_path, "rb") as file:
                files = {"files": file}
                response = requests.post(url, headers=self.headers, files=files)
        except FileNotFoundError as e:
            raise ApiHubClientException(f"File not found: {file_path}", None) from e

        self.logger.debug("Request Headers Sent: %s", response.request.headers)
        self.logger.debug("Request URL: %s", response.request.url)

        if response.status_code != 200:
            self.logger.error("Processing failed: %s", response.text)
            raise ApiHubClientException(response.text, response.status_code)

        data = response.json()
        execution_id = data.get("execution_id")

        # If execution_id is not directly available, try to extract from status_api
        if not execution_id:
            status_api = data.get("message", {}).get("status_api")
            if status_api:
                execution_id = self._extract_execution_id_from_url(status_api)

        self.logger.info(
            "Processing started successfully. Execution ID: %s", execution_id
        )

        # If wait_for_completion is True, poll for status and return final result
        if wait_for_completion:
            if not execution_id:
                self.logger.warning(
                    "No execution_id in response, returning initial data"
                )
                return data

            return self.wait_for_completion(
                endpoint,
                execution_id,
                polling_interval=polling_interval,
                timeout=timeout,
            )

        return data

    def get_result(self, endpoint: str, execution_id: str) -> dict:
        """
        Get the result of a processing operation.

        Args:
            endpoint: The endpoint name used for processing
            execution_id: The execution ID to get results for

        Returns:
            dict: Processing result or status information

        Raises:
            ApiHubClientException: If result retrieval fails
        """
        url = f"{self.base_url}/api/v1/{endpoint}"
        params = {"execution_id": execution_id}

        self.logger.debug(
            "Getting result for endpoint %s, execution ID: %s", endpoint, execution_id
        )
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code == 422:
            # Handle 422 status which may indicate processing in progress
            try:
                data = response.json()
                if "status" in data:
                    return data
            except (ValueError, KeyError):
                # JSON parsing failed or status key missing, treat as error
                pass
            raise ApiHubClientException(response.text, response.status_code)
        elif response.status_code != 200:
            raise ApiHubClientException(response.text, response.status_code)

        return response.json()

    def wait_for_completion(
        self,
        endpoint: str,
        execution_id: str,
        timeout: int = 600,
        polling_interval: int = 3,
    ) -> dict:
        """
        Wait for a processing operation to complete by polling its status.

        Args:
            endpoint: The endpoint name used for processing
            execution_id: The execution ID to wait for
            timeout: Maximum time to wait in seconds (default: 600)
            polling_interval: Seconds to wait between status checks (default: 3)

        Returns:
            dict: Final processing result when completed

        Raises:
            ApiHubClientException: If processing fails or times out
        """
        self.logger.info(
            "Waiting for completion. Polling every %d seconds", polling_interval
        )
        start_time = time.time()

        while time.time() - start_time < timeout:
            result = self.get_result(endpoint, execution_id)
            status = result.get("status")
            self.logger.info("Current status: %s", status)

            # Check for completion - different APIs may use different status values
            if status in ["COMPLETED", "SUCCESS", "FINISHED"]:
                self.logger.info("Processing completed")
                return result
            elif status in ["FAILED", "ERROR"]:
                self.logger.error("Processing failed")
                error_message = result.get("error", "Unknown error")
                raise ApiHubClientException(
                    (
                        f"Processing failed for execution_id: {execution_id}. "
                        f"Error: {error_message}"
                    ),
                    None,
                )
            elif status in ["PROCESSING", "IN_PROGRESS", "RUNNING", "EXECUTING"]:
                # Continue polling
                pass
            else:
                # For unknown status, assume it's still processing
                self.logger.debug("Unknown status: %s, continuing to poll", status)

            time.sleep(polling_interval)

        # If we reach here, we've timed out
        raise ApiHubClientException(
            f"Timeout waiting for completion. Execution ID: {execution_id}",
            None,
        )

    def check_status(self, endpoint: str, execution_id: str) -> str | None:
        """
        Check the current status of a processing operation.

        Args:
            endpoint: The endpoint name used for processing
            execution_id: The execution ID to check status for

        Returns:
            str | None: Current status string, or None if not available

        Raises:
            ApiHubClientException: If status check fails
        """
        try:
            result = self.get_result(endpoint, execution_id)
            return result.get("status")
        except ApiHubClientException:
            # Re-raise the exception to let caller handle it
            raise
