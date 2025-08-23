import logging
import time
from pathlib import Path

import requests

from .client import ApiHubClientException


class DocSplitterClient:
    """
    Client for interacting with doc-splitter APIs.

    Handles document splitting operations including file upload,
    job status monitoring, and result download.
    """

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        api_key: str,
        base_url: str,
    ) -> None:
        """
        Initialize the DocSplitterClient.

        Args:
            api_key: API key for authentication
            base_url: Base URL of the doc-splitter service
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.headers = {"apikey": self.api_key}

    def upload(
        self,
        file_path: str,
        wait_for_completion: bool = False,
        polling_interval: int = 5,
    ) -> dict:
        """
        Upload a document for splitting.

        Args:
            file_path: Path to the file to upload
            wait_for_completion: If True, polls for completion and returns final result
            polling_interval: Seconds to wait between status checks (default: 5)

        Returns:
            dict: Response containing job_id and status information

        Raises:
            ApiHubClientException: If upload fails
        """
        url = f"{self.base_url}/api/v1/doc-splitter/documents/upload"

        self.logger.info("Uploading file for splitting: %s", file_path)

        try:
            with open(file_path, "rb") as file:
                files = {"file": file}
                response = requests.post(url, headers=self.headers, files=files)
        except FileNotFoundError as e:
            raise ApiHubClientException(f"File not found: {file_path}", None) from e

        self.logger.debug("Request Headers Sent: %s", response.request.headers)
        self.logger.debug("Request URL: %s", response.request.url)

        if response.status_code not in [200, 202]:
            self.logger.error("Upload failed: %s", response.text)
            raise ApiHubClientException(response.text, response.status_code)

        data = response.json()
        # Extract job_id from the nested data structure
        if "data" in data and isinstance(data["data"], dict):
            job_id = data["data"].get("job_id")
        else:
            job_id = data.get("job_id")
        self.logger.info("Upload completed successfully. Job ID: %s", job_id)

        # If wait_for_completion is True, poll for status and return final result
        if wait_for_completion:
            if not job_id:
                self.logger.warning("No job_id in response, returning initial data")
                return data

            return self.wait_for_completion(job_id, polling_interval=polling_interval)

        return data

    def get_job_status(self, job_id: str) -> dict:
        """
        Check the status of a splitting job.

        Args:
            job_id: The job ID to check status for

        Returns:
            dict: Status information

        Raises:
            ApiHubClientException: If status check fails
        """
        url = f"{self.base_url}/api/v1/doc-splitter/jobs/status"
        params = {"job_id": job_id}

        self.logger.debug("Checking status for job ID: %s", job_id)
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise ApiHubClientException(response.text, response.status_code)

        return response.json()

    def download_result(self, job_id: str, output_path: str | None = None) -> str:
        """
        Download the result of a completed splitting job.

        Args:
            job_id: The job ID to download results for
            output_path: Path where to save the downloaded file.
                        If None, uses 'result_{job_id}.zip'

        Returns:
            str: Path to the downloaded file

        Raises:
            ApiHubClientException: If download fails
        """
        url = f"{self.base_url}/api/v1/doc-splitter/jobs/download"
        params = {"job_id": job_id}

        if output_path is None:
            output_path = f"result_{job_id}.zip"

        self.logger.info("Downloading result for job ID: %s to %s", job_id, output_path)
        response = requests.get(url, headers=self.headers, params=params, stream=True)

        if response.status_code != 200:
            raise ApiHubClientException(response.text, response.status_code)

        # Ensure output directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        self.logger.info("Download completed: %s", output_path)
        return output_path

    def wait_for_completion(
        self, job_id: str, timeout: int = 600, polling_interval: int = 3
    ) -> dict:
        """
        Wait for a splitting job to complete by polling its status.

        Args:
            job_id: The job ID to wait for
            timeout: Maximum time to wait in seconds (default: 600)
            polling_interval: Seconds to wait between status checks (default: 3)

        Returns:
            dict: Final job status information when completed

        Raises:
            ApiHubClientException: If processing fails or times out
        """
        self.logger.info(
            "Waiting for completion. Polling every %d seconds", polling_interval
        )
        start_time = time.time()

        while time.time() - start_time < timeout:
            status_result = self.get_job_status(job_id)
            # Extract status from nested data structure
            if "data" in status_result and isinstance(status_result["data"], dict):
                status = status_result["data"].get("status")
            else:
                status = status_result.get("status")
            self.logger.info("Current status: %s", status)

            if status and status.upper() == "COMPLETED":
                self.logger.info("Processing completed")
                return status_result
            elif status and status.upper() == "FAILED":
                self.logger.error("Processing failed")
                raise ApiHubClientException(
                    f"Processing failed for job_id: {job_id}",
                    None,
                )

            time.sleep(polling_interval)

        # If we reach here, we've timed out
        raise ApiHubClientException(
            f"Timeout waiting for completion. Job ID: {job_id}",
            None,
        )
