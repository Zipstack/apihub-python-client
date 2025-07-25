import logging
import time

import requests


class ApiHubClientException(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code

    def __str__(self):
        return repr(f"Message: {self.message}, Status Code: {self.status_code}")


class ApiHubClient:
    logger = logging.getLogger(__name__)

    def __init__(
        self,
        api_key: str,
        base_url: str,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

        self.headers = {"apikey": self.api_key}

    def extract(
        self,
        endpoint: str,
        vertical: str,
        sub_vertical: str,
        file_path: str | None = None,
        file_hash: str | None = None,
        wait_for_completion: bool = False,
        polling_interval: int = 5,
        **kwargs,
    ) -> dict:
        """
        Generic extract function that handles both discover and extract operations.

        Args:
            endpoint: The endpoint name (e.g., 'discover_tables', 'extract_table')
            vertical: Required vertical parameter
            sub_vertical: Required sub_vertical parameter
            file_path: Path to file for upload (for discover operations)
            file_hash: File hash for cached operations (for extract operations)
            wait_for_completion: If True, polls for completion and returns final result
            polling_interval: Seconds to wait between status checks (default: 5)
            **kwargs: Additional query parameters
        """
        url = f"{self.base_url}/extract/{endpoint}"
        params = {"vertical": vertical, "sub_vertical": sub_vertical, **kwargs}

        # Add file_hash if provided (for extract operations)
        if file_hash:
            params["use_cached_file_hash"] = file_hash

        self.logger.debug("Headers: %s", self.headers)
        self.logger.debug("Params: %s", params)

        # Handle file upload for discover operations
        if file_path:
            self.logger.info("Uploading file to extract: %s", file_path)
            # Add Content-Type header for file upload
            with open(file_path, "rb") as file:
                response = requests.post(
                    url, headers=self.headers, params=params, data=file.read()
                )
        else:
            # For cached file operations
            response = requests.post(url, headers=self.headers, params=params)

        self.logger.debug("Request Headers Sent: %s", response.request.headers)
        self.logger.debug("Request Path URL: %s", response.request.path_url)

        if response.status_code != 200:
            self.logger.error("Operation failed: %s", response.text)
            raise ApiHubClientException(response.text, response.status_code)

        data = response.json()
        self.logger.info(
            "Operation completed successfully. File hash: %s", data.get("file_hash")
        )

        # If wait_for_completion is True, poll for status and return final result
        if wait_for_completion:
            file_hash_for_polling = data.get("file_hash")
            if not file_hash_for_polling:
                self.logger.warning("No file_hash in response, returning initial data")
                return data

            return self.wait_for_complete(
                file_hash_for_polling, polling_interval=polling_interval
            )

        return data

    def wait_for_complete(
        self, file_hash: str, timeout: int = 600, polling_interval: int = 3
    ) -> dict:
        """
        Wait for extraction job to complete by polling status.

        Args:
            file_hash: The file hash to check status for
            timeout: Maximum time to wait in seconds (default: 600)
            polling_interval: Seconds to wait between status checks (default: 3)

        Returns:
            The final extraction result

        Raises:
            ApiHubClientException: If processing fails or times out
        """
        self.logger.info(
            "Waiting for completion. Polling every %d seconds", polling_interval
        )
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_result = self.get_status(file_hash)
            status = status_result.get("status")
            self.logger.info("Current status: %s", status)

            if status == "COMPLETED":
                self.logger.info("Processing completed. Retrieving final result")
                return self.retrieve(file_hash)
            elif status == "FAILED":
                self.logger.error("Processing failed")
                raise ApiHubClientException(
                    f"Processing failed for file_hash: {file_hash}",
                    None,
                )

            time.sleep(polling_interval)

        # If we reach here, we've timed out
        raise ApiHubClientException(
            f"Timeout waiting for completion. File hash: {file_hash}",
            None,
        )

    def get_status(self, file_hash: str) -> dict:
        """Check status of the extraction job"""
        url = f"{self.base_url}/status"
        params = {"file_hash": file_hash}

        self.logger.debug("Checking status for file hash: %s", file_hash)
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise ApiHubClientException(response.text, response.status_code)

        return response.json()

    def retrieve(self, file_hash: str) -> dict:
        """Retrieve result for completed extraction"""
        url = f"{self.base_url}/retrieve"
        params = {"file_hash": file_hash}

        self.logger.info("Retrieving result for file hash: %s", file_hash)
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise ApiHubClientException(response.text, response.status_code)

        return response.json()
