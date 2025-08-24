# Unstract API Hub Python Client

A Python client for the Unstract ApiHub service that provides a clean, Pythonic interface for document processing APIs following the extract → status → retrieve pattern.

[![Python Version](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![PyPI Version](https://img.shields.io/pypi/v/apihub-python-client)](https://pypi.org/project/apihub-python-client/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/Zipstack/apihub-python-client)
[![PyPI Downloads](https://img.shields.io/pypi/dm/apihub-python-client)](https://pypi.org/project/apihub-python-client/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## 🚀 Features

- **Simple API Interface**: Clean, easy-to-use client for Unstract ApiHub services
- **File Processing**: Support for document processing with file uploads
- **Status Monitoring**: Track processing status with polling capabilities
- **Error Handling**: Comprehensive exception handling with meaningful messages
- **Flexible Parameters**: Support for custom parameters and configurations
- **Automatic Polling**: Optional wait-for-completion functionality
- **Type Safety**: Full type hints for better development experience

## 📦 Installation

```bash
pip install apihub-python-client
```

Or install from source:

```bash
git clone https://github.com/Zipstack/apihub-python-client.git
cd apihub-python-client
pip install -e .
```

## 🎯 Quick Start

### Basic Usage

```python
from apihub_client import ApiHubClient

# Initialize the client
client = ApiHubClient(
    api_key="your-api-key-here",
    base_url="https://api-hub.us-central.unstract.com/api/v1"
)

# Process a document with automatic completion waiting
result = client.extract(
    endpoint="bank_statement",
    vertical="table",
    sub_vertical="bank_statement",
    file_path="statement.pdf",
    wait_for_completion=True,
    polling_interval=3  # Check status every 3 seconds
)

print("Processing completed!")
print(result)
```

## 🛠️ Common Use Cases

### Document Splitter API

Split documents into smaller parts using the doc-splitter service:

```python
from apihub_client import DocSplitterClient

# Initialize the doc-splitter client
doc_client = DocSplitterClient(
    api_key="your-api-key-here",
    base_url="http://localhost:8005"
)

# Simple upload and wait for completion
result = doc_client.upload(
    file_path="large_document.pdf",
    wait_for_completion=True,
    polling_interval=5  # Check status every 5 seconds
)

# Download the split result
output_file = doc_client.download_result(
    job_id=result["job_id"],
    output_path="split_result.zip"
)
print(f"Downloaded result to: {output_file}")
```

#### Step-by-Step Doc-Splitter Processing

```python
# Step 1: Upload document
upload_result = doc_client.upload(file_path="document.pdf")
job_id = upload_result["job_id"]
print(f"Upload completed. Job ID: {job_id}")

# Step 2: Monitor status manually
status = doc_client.get_job_status(job_id)
print(f"Current status: {status['status']}")

# Step 3: Wait for completion (with custom timeout)
final_result = doc_client.wait_for_completion(
    job_id=job_id,
    timeout=600,        # Wait up to 10 minutes
    polling_interval=3  # Check every 3 seconds
)

# Step 4: Download the processed result
downloaded_file = doc_client.download_result(
    job_id=job_id,
    output_path="processed_document.zip"
)
print(f"Processing complete! Downloaded: {downloaded_file}")
```

#### Batch Processing with Doc-Splitter

```python
import os
from pathlib import Path

def process_documents_batch(file_paths):
    """Process multiple documents with doc-splitter."""
    results = []

    for file_path in file_paths:
        try:
            print(f"Processing {file_path}...")

            # Upload and wait for completion
            result = doc_client.upload(
                file_path=file_path,
                wait_for_completion=True,
                polling_interval=5
            )

            # Generate output filename
            input_name = Path(file_path).stem
            output_path = f"{input_name}_split.zip"

            # Download result
            downloaded_file = doc_client.download_result(
                job_id=result["job_id"],
                output_path=output_path
            )

            results.append({
                "input": file_path,
                "output": downloaded_file,
                "job_id": result["job_id"],
                "success": True
            })

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")
            results.append({
                "input": file_path,
                "error": str(e),
                "success": False
            })

    return results

# Process multiple files
files = ["document1.pdf", "document2.pdf", "document3.pdf"]
results = process_documents_batch(files)

# Summary
successful = [r for r in results if r["success"]]
failed = [r for r in results if not r["success"]]
print(f"Processed: {len(successful)} successful, {len(failed)} failed")
```

### Generic Unstract API

Process documents using dynamic endpoints like invoice, contract, receipt, etc.:

```python
from apihub_client import GenericUnstractClient

# Initialize the generic client
client = GenericUnstractClient(
    api_key="your-api-key-here",
    base_url="http://localhost:8005"
)

# Simple processing with automatic completion waiting
result = client.process(
    endpoint="invoice",
    file_path="invoice.pdf",
    wait_for_completion=True,
    polling_interval=5  # Check status every 5 seconds
)
print("Invoice processing completed:", result)
```

#### Step-by-Step Generic API Processing

```python
# Step 1: Start processing
process_result = client.process(
    endpoint="contract",
    file_path="contract.pdf"
)
execution_id = process_result["execution_id"]
print(f"Processing started. Execution ID: {execution_id}")

# Step 2: Check status manually
status = client.check_status("contract", execution_id)
print(f"Current status: {status}")

# Step 3: Wait for completion (with custom timeout)
final_result = client.wait_for_completion(
    endpoint="contract",
    execution_id=execution_id,
    timeout=600,        # Wait up to 10 minutes
    polling_interval=3  # Check every 3 seconds
)

# Step 4: Get result later (if needed)
result = client.get_result("contract", execution_id)
print("Processing complete:", result)
```

#### Batch Processing with Generic APIs

```python
def process_documents_batch(endpoint, file_paths):
    """Process multiple documents with the same endpoint."""
    results = []

    for file_path in file_paths:
        try:
            print(f"Processing {file_path} with {endpoint} endpoint...")

            # Process and wait for completion
            result = client.process(
                endpoint=endpoint,
                file_path=file_path,
                wait_for_completion=True,
                polling_interval=5
            )

            results.append({
                "input": file_path,
                "execution_id": result["execution_id"],
                "result": result,
                "success": True
            })

        except Exception as e:
            print(f"Failed to process {file_path}: {e}")
            results.append({
                "input": file_path,
                "error": str(e),
                "success": False
            })

    return results

# Process multiple invoices
invoice_files = ["invoice1.pdf", "invoice2.pdf", "invoice3.pdf"]
results = process_documents_batch("invoice", invoice_files)

# Process multiple contracts
contract_files = ["contract1.pdf", "contract2.pdf"]
contract_results = process_documents_batch("contract", contract_files)

# Summary
successful = [r for r in results if r["success"]]
failed = [r for r in results if not r["success"]]
print(f"Processed: {len(successful)} successful, {len(failed)} failed")
```

### Integration: Doc-Splitter + Extraction APIs

Combine doc-splitter with extraction APIs for complete document processing:

```python
from apihub_client import ApiHubClient, DocSplitterClient

# Initialize both clients
api_client = ApiHubClient(
    api_key="your-api-key",
    base_url="https://api-hub.us-central.unstract.com/api/v1"
)

doc_splitter = DocSplitterClient(
    api_key="your-api-key",
    base_url="http://localhost:8005"
)

# Step 1: Split the large document
split_result = doc_splitter.upload(
    file_path="large_contract.pdf",
    wait_for_completion=True
)

# Step 2: Download split result
doc_splitter.download_result(
    job_id=split_result["job_id"],
    output_path="split_documents.zip"
)

# Step 3: Process individual documents (example with one document)
# (assuming you extract individual PDFs from the zip)
table_result = api_client.extract(
    endpoint="bank_statement",
    vertical="table",
    sub_vertical="bank_statement",
    file_path="individual_page.pdf",
    wait_for_completion=True
)
print("Extracted data:", table_result)
```

### Complete Workflow: All Three Clients

```python
from apihub_client import ApiHubClient, DocSplitterClient, GenericUnstractClient

# Initialize all clients
api_client = ApiHubClient(
    api_key="your-api-key",
    base_url="https://api-hub.us-central.unstract.com/api/v1"
)

doc_splitter = DocSplitterClient(
    api_key="your-api-key",
    base_url="http://localhost:8005"
)

generic_client = GenericUnstractClient(
    api_key="your-api-key",
    base_url="http://localhost:8005"
)

# Workflow: Split → Extract → Process with Generic API
# Step 1: Split large document
split_result = doc_splitter.upload(
    file_path="large_document.pdf",
    wait_for_completion=True
)

# Step 2: Extract tables from split documents
# (after extracting individual files from the zip)
table_result = api_client.extract(
    endpoint="discover_tables",
    vertical="table",
    sub_vertical="discover_tables",
    file_path="split_page_1.pdf",
    wait_for_completion=True
)

# Step 3: Process with generic invoice API
invoice_result = generic_client.process(
    endpoint="invoice",
    file_path="split_page_2.pdf",
    wait_for_completion=True
)

print("Complete workflow finished!")
print("Tables extracted:", len(table_result.get('data', [])))
print("Invoice processed:", invoice_result.get('execution_id'))
```

### All Table Extraction API

```python

    # Step 1: Discover tables from the uploaded PDF
    initial_result = client.extract(
        endpoint="discover_tables",
        vertical="table",
        sub_vertical="discover_tables",
        ext_cache_result="true",
        ext_cache_text="true",
        file_path="statement.pdf"
    )
    file_hash = initial_result.get("file_hash")
    print("File hash", file_hash)
    discover_tables_result = client.wait_for_complete(file_hash,
        timeout=600, # max wait for 10 mins
        polling_interval=3 # polling every 3s
    )

    tables = json.loads(discover_tables_result['data'])
    print(f"Total tables in this document: {len(tables)}")

    all_table_result = []
    # Step 2: Extract specific table
    for i, table in enumerate(tables):
        table_result = client.extract(
            endpoint="extract_table",
            vertical="table",
            sub_vertical="extract_table",
            file_hash=file_hash,
            ext_table_no=i, # extracting nth table
            wait_for_completion=True
        )

        print(f"Extracted table : {table['table_name']}")
        all_table_result.append({table["table_name"]: table_result})

    print("All table result")
    print(all_table_result)

```

### Bank Statement Extraction API

```python
# Process bank statement
result = client.extract(
    endpoint="bank_statement",
    vertical="table",
    sub_vertical="bank_statement",
    file_path="bank_statement.pdf",
    wait_for_completion=True,
    polling_interval=3
)

print("Bank statement processed:", result)
```

### Step-by-Step Processing

```python
# Step 1: Start processing
initial_result = client.extract(
    endpoint="discover_tables",
    vertical="table",
    sub_vertical="discover_tables",
    file_path="document.pdf"
)

file_hash = initial_result["file_hash"]
print(f"Processing started with hash: {file_hash}")

# Step 2: Monitor status
status = client.get_status(file_hash)
print(f"Current status: {status['status']}")

# Step 3: Wait for completion (using wait_for_complete method)
final_result = client.wait_for_complete(
    file_hash=file_hash,
    timeout=600,        # Wait up to 10 minutes
    polling_interval=3  # Check every 3 seconds
)
print("Final result:", final_result)

```

### Using Cached Files

Once a file has been processed, you can reuse it by file hash:

```python
# Process a different operation on the same file
table_result = client.extract(
    endpoint="extract_table",
    vertical="table",
    sub_vertical="extract_table",
    file_hash="previously-obtained-hash",
    ext_table_no=1,  # Extract second table. Indexing starts at 0
    wait_for_completion=True
)
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
API_KEY=your_api_key_here
BASE_URL=https://api.example.com
LOG_LEVEL=INFO
```

Then load in your code:

```python
import os
from dotenv import load_dotenv
from apihub_client import ApiHubClient

load_dotenv()

client = ApiHubClient(
    api_key=os.getenv("API_KEY"),
    base_url=os.getenv("BASE_URL")
)
```

## 📚 API Reference

### ApiHubClient

The main client class for interacting with the ApiHub service.

```python
client = ApiHubClient(api_key: str, base_url: str)
```

**Parameters:**

- `api_key` (str): Your API key for authentication
- `base_url` (str): The base URL of the ApiHub service

### DocSplitterClient

Client for interacting with doc-splitter APIs for document splitting operations.

```python
doc_client = DocSplitterClient(api_key: str, base_url: str)
```

**Parameters:**

- `api_key` (str): Your API key for authentication
- `base_url` (str): The base URL of the doc-splitter service

### GenericUnstractClient

Client for interacting with generic Unstract APIs using dynamic endpoints.

```python
generic_client = GenericUnstractClient(api_key: str, base_url: str)
```

**Parameters:**

- `api_key` (str): Your API key for authentication
- `base_url` (str): The base URL of the Unstract service

#### Methods

##### extract()

Start a document processing operation.

```python
extract(
    endpoint: str,
    vertical: str,
    sub_vertical: str,
    file_path: str | None = None,
    file_hash: str | None = None,
    wait_for_completion: bool = False,
    polling_interval: int = 5,
    **kwargs
) -> dict
```

**Parameters:**

- `endpoint` (str): The API endpoint to call (e.g., "discover_tables", "extract_table")
- `vertical` (str): The processing vertical
- `sub_vertical` (str): The processing sub-vertical
- `file_path` (str, optional): Path to file for upload (for new files)
- `file_hash` (str, optional): Hash of previously uploaded file (for cached operations)
- `wait_for_completion` (bool): If True, polls until completion and returns final result
- `polling_interval` (int): Seconds between status checks when waiting (default: 5)
- `**kwargs`: Additional parameters specific to the endpoint

**Returns:**

- `dict`: API response containing processing results or file hash for tracking

##### get_status()

Check the status of a processing job.

```python
get_status(file_hash: str) -> dict
```

**Parameters:**

- `file_hash` (str): The file hash returned from extract()

**Returns:**

- `dict`: Status information including current processing state

##### retrieve()

Get the final results of a completed processing job.

```python
retrieve(file_hash: str) -> dict
```

**Parameters:**

- `file_hash` (str): The file hash of the completed job

**Returns:**

- `dict`: Final processing results

##### wait_for_complete()

Wait for a processing job to complete by polling its status.

```python
wait_for_complete(
    file_hash: str,
    timeout: int = 600,
    polling_interval: int = 3
) -> dict
```

**Parameters:**

- `file_hash` (str): The file hash of the job to wait for
- `timeout` (int): Maximum time to wait in seconds (default: 600)
- `polling_interval` (int): Seconds between status checks (default: 3)

**Returns:**

- `dict`: Final processing results when completed

**Raises:**

- `ApiHubClientException`: If processing fails or times out

#### DocSplitterClient Methods

##### upload()

Upload a document for splitting.

```python
upload(
    file_path: str,
    wait_for_completion: bool = False,
    polling_interval: int = 5,
) -> dict
```

**Parameters:**

- `file_path` (str): Path to the file to upload
- `wait_for_completion` (bool): If True, polls until completion and returns final result
- `polling_interval` (int): Seconds between status checks when waiting (default: 5)

**Returns:**

- `dict`: Response containing job_id and status information

##### get_job_status()

Check the status of a splitting job.

```python
get_job_status(job_id: str) -> dict
```

**Parameters:**

- `job_id` (str): The job ID to check status for

**Returns:**

- `dict`: Status information including current processing state

##### download_result()

Download the result of a completed splitting job.

```python
download_result(
    job_id: str,
    output_path: str | None = None
) -> str
```

**Parameters:**

- `job_id` (str): The job ID to download results for
- `output_path` (str, optional): Path where to save the downloaded file. If None, uses 'result\_{job_id}.zip'

**Returns:**

- `str`: Path to the downloaded file

##### wait_for_completion()

Wait for a splitting job to complete by polling its status.

```python
wait_for_completion(
    job_id: str,
    timeout: int = 600,
    polling_interval: int = 3
) -> dict
```

**Parameters:**

- `job_id` (str): The job ID to wait for
- `timeout` (int): Maximum time to wait in seconds (default: 600)
- `polling_interval` (int): Seconds between status checks (default: 3)

**Returns:**

- `dict`: Final job status information when completed

**Raises:**

- `ApiHubClientException`: If processing fails or times out

#### GenericUnstractClient Methods

##### process()

Process a document using the specified endpoint.

```python
process(
    endpoint: str,
    file_path: str,
    wait_for_completion: bool = False,
    polling_interval: int = 5,
    timeout: int = 600,
) -> dict
```

**Parameters:**

- `endpoint` (str): The endpoint name (e.g., 'invoice', 'contract', 'receipt')
- `file_path` (str): Path to the file to upload
- `wait_for_completion` (bool): If True, polls until completion and returns final result
- `polling_interval` (int): Seconds between status checks when waiting (default: 5)
- `timeout` (int): Maximum time to wait for completion in seconds (default: 600)

**Returns:**

- `dict`: Response containing execution_id and processing information

##### get_result()

Get the result of a processing operation.

```python
get_result(endpoint: str, execution_id: str) -> dict
```

**Parameters:**

- `endpoint` (str): The endpoint name used for processing
- `execution_id` (str): The execution ID to get results for

**Returns:**

- `dict`: Processing result or status information

##### wait_for_completion()

Wait for a processing operation to complete by polling its status.

```python
wait_for_completion(
    endpoint: str,
    execution_id: str,
    timeout: int = 600,
    polling_interval: int = 3,
) -> dict
```

**Parameters:**

- `endpoint` (str): The endpoint name used for processing
- `execution_id` (str): The execution ID to wait for
- `timeout` (int): Maximum time to wait in seconds (default: 600)
- `polling_interval` (int): Seconds between status checks (default: 3)

**Returns:**

- `dict`: Final processing result when completed

##### check_status()

Check the current status of a processing operation.

```python
check_status(endpoint: str, execution_id: str) -> str | None
```

**Parameters:**

- `endpoint` (str): The endpoint name used for processing
- `execution_id` (str): The execution ID to check status for

**Returns:**

- `str | None`: Current status string, or None if not available

**Raises:**

- `ApiHubClientException`: If processing fails or times out

### Exception Handling

All clients (`ApiHubClient`, `DocSplitterClient`, and `GenericUnstractClient`) use the same exception handling:

```python
from apihub_client import ApiHubClientException, GenericUnstractClient

generic_client = GenericUnstractClient(api_key="key", base_url="http://localhost:8005")

try:
    result = generic_client.process(
        endpoint="invoice",
        file_path="invoice.pdf",
        wait_for_completion=True
    )

    print("Processing completed:", result["execution_id"])

except ApiHubClientException as e:
    print(f"Error: {e.message}")
    print(f"Status Code: {e.status_code}")
```

### Batch Processing

```python
import time
from pathlib import Path

def process_documents(file_paths, endpoint):
    results = []

    for file_path in file_paths:
        try:
            print(f"Processing {file_path}...")
            # Start processing
            initial_result = client.extract(
                endpoint=endpoint,
                vertical="table",
                sub_vertical=endpoint,
                file_path=file_path
            )

            # Wait for completion with custom settings
            result = client.wait_for_complete(
                file_hash=initial_result["file_hash"],
                timeout=900,        # 15 minutes for batch processing
                polling_interval=5  # Less frequent polling for batch
            )
            results.append({"file": file_path, "result": result, "success": True})

        except ApiHubClientException as e:
            print(f"Failed to process {file_path}: {e.message}")
            results.append({"file": file_path, "error": str(e), "success": False})

    return results

# Process multiple files
file_paths = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
results = process_documents(file_paths, "bank_statement")

# Summary
successful = [r for r in results if r["success"]]
failed = [r for r in results if not r["success"]]

print(f"Processed: {len(successful)} successful, {len(failed)} failed")
```

## 🧪 Testing

Run the test suite:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run tests with coverage
pytest --cov=apihub_client --cov-report=html

# Run specific test files
pytest test/test_client.py -v
pytest test/test_integration.py -v
```

### Integration Testing

For integration tests with a real API:

```bash
# Create .env file with real credentials
cp .env.example .env
# Edit .env with your API credentials

# Run integration tests
pytest test/test_integration.py -v
```

## 🔍 Logging

Enable debug logging to see detailed request/response information:

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

client = ApiHubClient(api_key="your-key", base_url="https://api.example.com")

# Now all API calls will show detailed logs
result = client.extract(...)
```

## 🚀 Releases

This project uses automated releases through GitHub Actions with PyPI Trusted Publishers for secure publishing.

### Creating a Release

1. **Go to GitHub Actions** → **"Release Tag and Publish Package"**
2. **Click "Run workflow"** and configure:
   - **Version bump**: `patch` (bug fixes), `minor` (new features), or `major` (breaking changes)
   - **Pre-release**: Check for beta/alpha versions
   - **Release notes**: Optional custom notes
3. **Click "Run workflow"** - the automation handles the rest!

The workflow will automatically:

- Update version in the code
- Create Git tags and GitHub releases
- Run all tests and quality checks
- Publish to PyPI using `uv publish` with Trusted Publishers

For more details, see [Release Documentation](.github/RELEASE.md).

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Zipstack/apihub-python-client.git
cd apihub-python-client

# Install dependencies using uv (required - do not use pip)
uv sync

# Install pre-commit hooks
uv run --frozen pre-commit install

# Run tests
uv run --frozen pytest

# Run linting and formatting
uv run --frozen ruff check .
uv run --frozen ruff format .

# Run type checking
uv run --frozen mypy src/

# Run all pre-commit hooks manually
uv run --frozen pre-commit run --all-files
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/Zipstack/apihub-python-client/issues)
- **Documentation**: Check this README and inline code documentation
- **Examples**: See the `examples/` directory for more usage patterns

## 📈 Version History

### v0.1.0

- Initial release
- Basic client functionality with extract, status, and retrieve operations
- File upload support
- Automatic polling with wait_for_completion
- Comprehensive test suite

---

Made with ❤️ by the Unstract team
